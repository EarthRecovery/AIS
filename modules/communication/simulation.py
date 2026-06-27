"""真实推演引擎：把"世界推进"变成实际跑场景对话 + 每轮世界裁判改状态。

一天 = 一串场景；每个场景跑若干轮对话；每一轮后由世界裁判更新所有在场角色的
记忆/所在地/物品/数值(hp/mp/stamina)/关系/认知；导演决定结束本幕、切下一幕或结束这天。
支持逐步(下一轮/下一幕)与一键自动跑完一天；每天开始拍快照，可回退一天。
"""

import re
from typing import Optional

from fastapi import Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.clients.llm_client import LLMClient
from modules.communication.service import CommunicationService
from modules.communication.world_service import WorldService
from modules.deps import get_llm_client
from modules.role.service import RoleService
from storage.db import get_db
from storage.models.character import Character
from storage.models.item import Item
from storage.models.location import Location
from storage.models.relationship import Relationship
from storage.models.manuscript import Manuscript
from storage.models.scene import Scene
from storage.models.scene_message import SceneMessage
from storage.models.scene_participant import SceneParticipant
from storage.models.world import World

MAX_ROUNDS_PER_SCENE = 3
MAX_SCENES_PER_DAY = 3


def _split_turn(text: str):
    """把一回合产出拆成 (say台词, do动作, think心理)。

    发言者默认只产出台词；仅在必要时用 §动作§ / §心理§ 标记在末尾追加。
    标记可任意顺序、可缺省；台词 = 第一个标记之前的部分。
    """
    t = (text or "").strip()
    parts = re.split(r"(§动作§|§心理§)", t)
    say = parts[0].strip()
    do = think = ""
    i = 1
    while i < len(parts) - 1:
        marker, seg = parts[i], parts[i + 1].strip()
        if marker == "§动作§":
            do = seg
        elif marker == "§心理§":
            think = seg
        i += 2
    return say, do, think


class SimulationService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client), db: AsyncSession = Depends(get_db)):
        self.llm = llm
        self.db = db
        self.cs = CommunicationService(llm=llm, db=db)
        self.ws = WorldService(llm=llm, db=db)
        self.roles = RoleService(db=db)

    # ---------------- 读取/状态 ----------------
    async def _get(self, model, id_):
        return (await self.db.execute(select(model).where(model.id == id_))).scalar_one_or_none()

    async def _active_scene(self, world_id) -> Optional[Scene]:
        return (await self.db.execute(
            select(Scene).where(Scene.world_id == world_id, Scene.status == "active")
            .order_by(Scene.id.desc()).limit(1))).scalar_one_or_none()

    async def status(self, world_id, recent_scenes=4):
        """演播室视图：只详载最近 recent_scenes 个场景的对话（长线推演防卡顿），
        更早的场景只给标题/状态（折叠，前端按需再拉对话）。"""
        world = await self._get(World, world_id)
        if world is None:
            return {"error": "世界不存在"}
        scenes = (await self.db.execute(
            select(Scene).where(Scene.world_id == world_id).order_by(Scene.id))).scalars().all()
        n = len(scenes)
        scene_blocks = []
        for i, s in enumerate(scenes):
            parts = await self.cs.get_participants(s.id)
            block = {
                "id": s.id, "name": s.name, "scenario": s.scenario, "status": s.status,
                "day_label": s.day_label, "participants": [p.role_name for p in parts],
            }
            if i >= n - recent_scenes:  # 最近若干幕：带完整对话
                msgs = await self.cs.get_messages(s.id)
                block["messages"] = [{"speaker_type": m.speaker_type, "speaker_name": m.speaker_name,
                                      "content": m.content, "kind": m.kind} for m in msgs]
                block["collapsed"] = False
            else:  # 更早的幕：折叠，只给条数
                cnt = (await self.db.execute(select(func.count()).select_from(SceneMessage)
                       .where(SceneMessage.scene_id == s.id))).scalar()
                block["messages"] = []
                block["message_count"] = int(cnt or 0)
                block["collapsed"] = True
            scene_blocks.append(block)
        chars = await self.ws._all(Character, world_id=world_id)
        char_state = []
        for c in chars:
            loc = await self._get(Location, c.current_location_id) if c.current_location_id else None
            char_state.append({"id": c.id, "name": c.name, "status": c.status,
                               "location": loc.name if loc else None, "stats": c.stats or {}})
        active = await self._active_scene(world_id)
        return {
            "world": {"id": world.id, "name": world.name, "in_world_time": world.in_world_time},
            "active_scene_id": active.id if active else None,
            "scenes": scene_blocks, "characters": char_state,
            "outline": world.outline or [], "beat_index": world.beat_index,
            "beat": self.ws._current_beat(world),
            "can_rollback": await self.ws.has_snapshot(world_id),
            "style_guide": world.style_guide or "",
        }

    async def scene_messages(self, scene_id):
        """按需拉取某个折叠场景的完整对话。"""
        msgs = await self.cs.get_messages(scene_id)
        return {"messages": [{"speaker_type": m.speaker_type, "speaker_name": m.speaker_name,
                              "content": m.content, "kind": m.kind} for m in msgs]}

    # ================= 写作层（MANUSCRIPT）：章节成稿 / 摘要 =================
    async def list_chapters(self, world_id):
        """按出现顺序列出各章节标签(= 场景 day_label)。"""
        scenes = (await self.db.execute(select(Scene).where(Scene.world_id == world_id)
                  .order_by(Scene.id))).scalars().all()
        seen, out = set(), []
        for s in scenes:
            lab = s.day_label or "未分章"
            if lab not in seen:
                seen.add(lab)
                out.append(lab)
        return out

    async def _chapter_material(self, world_id, label):
        """汇集某章节的全部场景 + 逐条消息(say/do/think/旁白) + 本章目标，供写作层使用。"""
        scenes = (await self.db.execute(select(Scene).where(
            Scene.world_id == world_id, Scene.day_label == label).order_by(Scene.id))).scalars().all()
        world = await self._get(World, world_id)
        goal = ""
        for b in (world.outline or []) if world else []:
            if b.get("title") and b["title"] in (label or ""):
                goal = b.get("goal", "")
                break
        out_scenes = []
        for s in scenes:
            msgs = await self.cs.get_messages(s.id)
            out_scenes.append({"name": s.name, "scenario": s.scenario,
                               "lines": [{"speaker": m.speaker_name, "kind": m.kind,
                                          "content": m.content} for m in msgs]})
        return {"label": label, "goal": goal, "scenes": out_scenes}

    async def summarize_chapter(self, world_id, label):
        mat = await self._chapter_material(world_id, label)
        return {"label": label, "summary": await self.llm.writing_summarize_chapter(mat)}

    async def write_chapters(self, world_id, labels=None):
        """把一个或多个章节写成小说散文(附摘要)；多章时用上一章摘要做前情衔接。"""
        world = await self._get(World, world_id)
        style = (world.style_guide or "") if world else ""
        labels = labels or await self.list_chapters(world_id)
        out, prev = [], ""
        for lab in labels:
            mat = await self._chapter_material(world_id, lab)
            summary = await self.llm.writing_summarize_chapter(mat)
            prose = await self.llm.writing_write_chapter(mat, style, prev)
            await self._save_manuscript(world_id, lab, summary, prose)   # 落稿
            out.append({"label": lab, "summary": summary, "prose": prose})
            prev = summary
        return out

    async def _save_manuscript(self, world_id, label, summary, content):
        """成稿落库：按 (world_id, chapter_label) upsert。"""
        row = (await self.db.execute(select(Manuscript).where(
            Manuscript.world_id == world_id,
            Manuscript.chapter_label == label))).scalar_one_or_none()
        if row:
            row.summary = summary
            row.content = content
        else:
            self.db.add(Manuscript(world_id=world_id, chapter_label=label,
                                   summary=summary, content=content))
        await self.db.commit()

    async def list_manuscripts(self, world_id):
        """读取已落库的成稿（按章节顺序）。"""
        rows = (await self.db.execute(select(Manuscript).where(Manuscript.world_id == world_id)
                .order_by(Manuscript.id))).scalars().all()
        return [{"label": r.chapter_label, "summary": r.summary, "prose": r.content} for r in rows]

    # ---------------- 章节 / 开场景 ----------------
    @staticmethod
    def _chapter_label(world):
        """当前章节名：优先用剧本大纲里该章的标题，否则「第N章」。"""
        outline = world.outline or []
        idx = world.beat_index or 0
        if outline and 0 <= idx < len(outline) and outline[idx].get("title"):
            return f"第{idx + 1}章 {outline[idx]['title']}"
        return f"第{idx + 1}章"

    async def open_scene(self, world_id, directive: str = "", snapshot: bool = True):
        world = await self._get(World, world_id)
        if world is None:
            return {"error": "世界不存在"}
        chapter = self._chapter_label(world)
        # 开新幕前拍快照（供「回退场景」）；step_round 已自行拍快照时传 snapshot=False 避免重复
        if snapshot:
            await self._snap(world_id)
        ctx, _, _, chars = await self.ws._director_context(world_id)

        # 结束当前进行中的场景，并为「下一幕」准备衔接上下文（尾段对话 + 各角色当前位置）
        cur = await self._active_scene(world_id)
        prev_scene = None
        if cur:
            tail_msgs = (await self.cs.get_messages(cur.id))[-6:]
            loc_bits = []
            for c in chars:
                loc = await self._get(Location, c.current_location_id) if c.current_location_id else None
                loc_bits.append(f"{c.name}@{loc.name if loc else '未知'}")
            prev_scene = {
                "name": cur.name,
                "recent": [{"speaker": m.speaker_name, "content": m.content} for m in tail_msgs],
                "locations": "，".join(loc_bits),
            }
            cur.status = "ended"
            await self.db.commit()

        plan = await self.llm.keeper_open_scene(ctx, directive, prev_scene)

        scene = Scene(user_id=world.user_id, world_id=world_id, worldview_id=world.worldview_id,
                      name=plan.get("name", "新场景"), scenario=plan.get("setting", ""),
                      status="active", day_label=chapter,
                      prev_scene_id=(cur.id if cur else None))
        self.db.add(scene)
        await self.db.commit()
        await self.db.refresh(scene)

        by_name = {c.name: c for c in chars}
        for order, nm in enumerate(plan.get("participants", []) or []):
            nm = (nm or "").strip()
            if not nm:
                continue
            ch = by_name.get(nm)
            # 导演引入的新登场者 → 自动建成真实角色（带状态，回退可净删）
            if ch is None:
                ch = await self.ws.create_character(world_id, nm)
                by_name[nm] = ch
                await self.ws.log_event(world_id, "character_spawn", f"新角色登场：{nm}",
                                        {}, actor=ch.id, in_world_time=chapter)
            self.db.add(SceneParticipant(scene_id=scene.id, role_id=ch.role_id,
                        character_id=ch.id, role_name=nm, display_order=order))
        await self.db.commit()
        await self.ws.log_event(world_id, "scene_open", f"开启场景：{scene.name}",
                                {"scene_id": scene.id}, in_world_time=chapter)
        return {"scene_id": scene.id, "name": scene.name, "scenario": scene.scenario,
                "participants": plan.get("participants", [])}

    async def new_chapter(self, world_id, directive: str = ""):
        """新建章节：拍快照(回退章节用) → 进入下一章 → 开本章第一幕。"""
        world = await self._get(World, world_id)
        if world is None:
            return {"error": "世界不存在"}
        # 拍快照（捕获当前章节进度，回退即恢复到此）
        await self._snap(world_id)
        # 结束当前场景，章节 +1
        cur = await self._active_scene(world_id)
        if cur:
            cur.status = "ended"
        await self.db.commit()
        # 章节末：把这一章的零散经历压缩并入各角色长期记忆（force）。
        # 一章内 self_summary 保持不变(缓存友好)，演化只发生在章节边界(可控、抗漂移)。
        await self._consolidate_chapter(world_id)
        world.beat_index = (world.beat_index or 0) + 1
        await self.db.commit()
        chapter = self._chapter_label(world)
        await self.ws.log_event(world_id, "chapter_new", f"进入{chapter}",
                                {"beat_index": world.beat_index}, in_world_time=chapter)
        opened = await self.open_scene(world_id, directive, snapshot=False)
        return {"chapter": chapter, "beat_index": world.beat_index, **opened}

    async def rollback_chapter(self, world_id):
        """回退章节：恢复最近一张快照（本章开篇前的状态）。"""
        return await self.ws.rollback_day(world_id)

    # ---------------- 跑一轮对话 + 世界裁判 ----------------
    async def _speaker_inputs(self, world_id, scene, part):
        """组装某个发言者的 prompt 输入：人格 + 世界观文本 + 感知(含短期/长期记忆)。"""
        wv = await self.cs.get_worldview(scene.worldview_id)
        worldview_text = self.cs._worldview_text(wv)
        # 注入沙盘参考文风，约束发言/叙述的语言风格
        world = await self._get(World, world_id)
        style = (world.style_guide or "").strip() if world else ""
        if style:
            worldview_text = (worldview_text + "\n\n【参考文风】请严格模仿以下文风来写这段发言/叙述：\n" + style).strip()
        persona = None
        if part.role_id:
            setting = await self.roles.get_role_setting_by_id(part.role_id)
            persona = setting.to_json() if setting else None
        persona = persona or {"name": part.role_name}
        perception = None
        if part.character_id:
            perception = await self.ws.build_perception(world_id, part.character_id, scene.id)
        return persona, worldview_text, perception

    async def _generate_line(self, world_id, scene, part, roster, transcript):
        persona, worldview_text, perception = await self._speaker_inputs(world_id, scene, part)
        text = ""
        async for chunk in self.llm.group_chat_stream_perceived(
                persona, worldview_text, scene.scenario, roster, transcript, perception,
                allow_actions=True):
            text += chunk
        return text.strip()

    async def _run_judge(self, world_id, scene, round_dialogue):
        """世界裁判结算这一轮，返回 (applied, end_scene, chapter_done)。

        章节按用户「新建章节」手动推进，这里不自动跳章；chapter_done 仅作提示。
        """
        chars = await self.ws._all(Character, world_id=world_id)
        by_name = {c.name: c for c in chars}
        ctx, _, _, _ = await self.ws._director_context(world_id)
        parts = await self.cs.get_participants(scene.id)
        char_state = []
        for p in parts:
            c = by_name.get(p.role_name)
            loc = await self._get(Location, c.current_location_id) if c and c.current_location_id else None
            char_state.append({"name": p.role_name, "location": loc.name if loc else None,
                               "stats": (c.stats if c else {}) or {},
                               "condition": (c.condition if c else None) or "正常",
                               "status": (c.status if c else "active")})
        # 剧本 + 本场景已进行轮数 → 让 Keeper 据此主动把控节奏
        beat = ctx.get("beat") if isinstance(ctx, dict) else None
        script = beat.get("script") if isinstance(beat, dict) else None
        all_msgs = await self.cs.get_messages(scene.id)
        say_n = sum(1 for m in all_msgs if m.kind == "say")
        round_index = say_n // max(1, len(parts))
        verdict = await self.llm.keeper_judge_round(ctx, scene.scenario, round_dialogue, char_state,
                                                    script=script, round_index=round_index)
        applied = await self._apply_verdict(world_id, scene, verdict, by_name)
        # Keeper 旁白：当剧情需要推进时由裁判直接促成的关键事件，记为旁白消息
        narration = (verdict.get("narration") or "").strip()
        if narration:
            await self.cs.add_message(scene.id, "narrator", "旁白", narration, kind="say")
            await self.ws.log_event(world_id, "narration", narration[:200],
                                    {"scene_id": scene.id}, in_world_time=self._chapter_label(
                                        await self._get(World, world_id)))
        sc = verdict.get("scene", {}) or {}
        end_scene = bool(sc.get("should_end") or sc.get("should_end_day"))
        chapter_done = bool(sc.get("beat_done"))
        if end_scene:
            scene.status = "ended"
            await self.db.commit()
            # 幕结束 → 给在场角色做记忆沉淀（保留最近 2 幕不沉淀）
            await self._consolidate_participants(world_id, scene)
        return applied, end_scene, chapter_done, narration

    async def _consolidate_participants(self, world_id, scene):
        """场景末「安全阀」：仅当某角色散记忆累计超过字数预算时才压缩(见 consolidate_character)。
        平时不压 → self_summary 整章稳定 → prompt 稳定前缀整章命中缓存。"""
        recent_ids = [s.id for s in (await self.db.execute(
            select(Scene).where(Scene.world_id == world_id)
            .order_by(Scene.id.desc()).limit(2))).scalars().all()]
        parts = await self.cs.get_participants(scene.id)
        for p in parts:
            if p.character_id:
                try:
                    await self.ws.consolidate_character(p.character_id, recent_ids)
                except Exception as e:
                    print(f"consolidate failed for {p.character_id}: {e}")

    async def _consolidate_chapter(self, world_id):
        """章节末：强制把整章经历折进各角色长期记忆(keep=[]，全部可沉淀)。"""
        chars = await self.ws._all(Character, world_id=world_id)
        for c in chars:
            try:
                await self.ws.consolidate_character(c.id, [], force=True)
            except Exception as e:
                print(f"chapter consolidate failed for {c.id}: {e}")

    async def _recent_transcript(self, world_id, limit_scenes=5):
        """上下文 = 最近 limit_scenes 个场景的全部对话（含当前场景），按时间顺序。"""
        scenes = (await self.db.execute(
            select(Scene).where(Scene.world_id == world_id)
            .order_by(Scene.id.desc()).limit(limit_scenes))).scalars().all()
        scenes = list(reversed(scenes))
        out = []
        for s in scenes:
            for m in await self.cs.get_messages(s.id):
                if m.kind == "think":
                    continue                          # 私有心理：不进共享上下文
                content = m.content if m.kind != "do" else f"（{m.speaker_name} {m.content}）"
                out.append({"speaker_name": m.speaker_name, "content": content})
        return out

    async def _snap(self, world_id):
        """推进前拍一张快照（供回退上一步/上一幕），并裁剪到最近若干张。"""
        await self.ws._snapshot_world(world_id)
        await self.ws.prune_snapshots(world_id)

    async def step_round(self, world_id, directive: str = ""):
        """跑一轮：每个在场角色各说一次 → 世界裁判结算状态 → 导演判断幕是否结束。"""
        await self._snap(world_id)
        scene = await self._active_scene(world_id)
        if scene is None:
            await self.open_scene(world_id, directive, snapshot=False)
            scene = await self._active_scene(world_id)
        if scene is None:
            return {"error": "无法开启场景"}

        parts = await self.cs.get_participants(scene.id)
        roster = await self.cs._build_roster(parts)
        round_dialogue = []
        for p in parts:
            transcript = await self._recent_transcript(world_id)
            text = await self._generate_line(world_id, scene, p, roster, transcript)
            say, do, think = _split_turn(text)
            if say:
                await self.cs.add_message(scene.id, "persona", p.role_name, say,
                                          speaker_role_id=p.role_id, kind="say")
            if do:
                await self.cs.add_message(scene.id, "persona", p.role_name, do,
                                          speaker_role_id=p.role_id, kind="do")
            if think:
                await self.cs.add_message(scene.id, "persona", p.role_name, think,
                                          speaker_role_id=p.role_id, kind="think")
            if say or do or think:
                round_dialogue.append({"speaker": p.role_name, "say": say, "do": do, "think": think})

        applied, end_scene, chapter_done, narration = await self._run_judge(world_id, scene, round_dialogue)
        return {"scene_id": scene.id, "round": round_dialogue, "applied": applied,
                "scene_ended": end_scene, "chapter_done": chapter_done, "narration": narration,
                "active_scene_id": (await self._active_scene(world_id) or scene).id if not end_scene else None}

    async def run_scene(self, world_id, directive: str = "", max_rounds=6):
        """单独开启对话、跑完一个场景（到裁判判定本幕结束或达上限）。"""
        if await self._active_scene(world_id) is None:
            await self.open_scene(world_id, directive)
        rounds = 0
        while rounds < max_rounds:
            res = await self.step_round(world_id, directive)
            rounds += 1
            if res.get("error") or res.get("scene_ended"):
                break
        return {"success": True, "rounds": rounds}

    async def step_round_stream(self, world_id, directive: str = ""):
        """流式版：逐 token 吐出每个角色的发言，最后吐裁判结算。yields 事件 dict。"""
        await self._snap(world_id)
        scene = await self._active_scene(world_id)
        newly_opened = False
        if scene is None:
            opened = await self.open_scene(world_id, directive, snapshot=False)
            if opened.get("error"):
                yield {"type": "error", "message": opened["error"]}
                return
            scene = await self._active_scene(world_id)
            newly_opened = True
        if scene is None:
            yield {"type": "error", "message": "无法开启场景"}
            return
        if newly_opened:
            p0 = await self.cs.get_participants(scene.id)
            yield {"type": "scene", "scene_id": scene.id, "name": scene.name,
                   "scenario": scene.scenario, "day_label": scene.day_label,
                   "participants": [p.role_name for p in p0]}

        parts = await self.cs.get_participants(scene.id)
        roster = await self.cs._build_roster(parts)
        round_dialogue = []
        for p in parts:
            transcript = await self._recent_transcript(world_id)
            persona, worldview_text, perception = await self._speaker_inputs(world_id, scene, p)
            yield {"type": "speaker", "name": p.role_name, "role_id": p.role_id}
            text = ""
            async for chunk in self.llm.group_chat_stream_perceived(
                    persona, worldview_text, scene.scenario, roster, transcript, perception,
                    allow_actions=True):
                text += chunk
                yield {"type": "token", "text": chunk}
            say, do, think = _split_turn(text)
            if say:
                await self.cs.add_message(scene.id, "persona", p.role_name, say,
                                          speaker_role_id=p.role_id, kind="say")
            if do:
                await self.cs.add_message(scene.id, "persona", p.role_name, do,
                                          speaker_role_id=p.role_id, kind="do")
            if think:
                await self.cs.add_message(scene.id, "persona", p.role_name, think,
                                          speaker_role_id=p.role_id, kind="think")
            if say or do or think:
                round_dialogue.append({"speaker": p.role_name, "say": say, "do": do, "think": think})
            yield {"type": "speaker_done", "name": p.role_name,
                   "say": say, "do": do, "think": think}

        yield {"type": "judging"}
        applied, end_scene, chapter_done, narration = await self._run_judge(world_id, scene, round_dialogue)
        if narration:
            yield {"type": "narration", "text": narration}
        yield {"type": "judge", "applied": applied,
               "scene_ended": end_scene, "chapter_done": chapter_done}
        yield {"type": "done"}

    async def _apply_verdict(self, world_id, scene, verdict, by_name):
        applied = {"memory": 0, "moves": 0, "stat_changes": 0, "items": 0,
                   "relationships": 0, "beliefs": 0, "mental": 0, "conditions": 0, "deaths": 0}
        day = scene.day_label
        for sc in verdict.get("state_changes", []):
            c = by_name.get(sc.get("character", ""))
            if c is None:
                continue
            # 情绪/目标/动机/自我摘要 → 更新心智状态
            mental_data = {k2: sc[k1] for k1, k2 in
                           (("mood", "mood"), ("goals", "goals"),
                            ("motivation", "motivation"), ("summary", "self_summary"))
                           if sc.get(k1)}
            if mental_data:
                ms = await self.ws.get_mental(c.id)
                if ms is None:
                    from storage.models.mental_state import MentalState
                    ms = MentalState(character_id=c.id)
                    self.db.add(ms)
                for k, v in mental_data.items():
                    setattr(ms, k, v)
                await self.db.commit()
                applied["mental"] += 1
            if sc.get("memory"):
                await self.ws.add_memory(world_id, c.id, sc["memory"], kind="memory", source_scene_id=scene.id, log=False)
                applied["memory"] += 1
            if sc.get("belief"):
                await self.ws.add_memory(world_id, c.id, sc["belief"], kind="belief", source_scene_id=scene.id, log=False)
                applied["beliefs"] += 1
            # 叙事状态短语（Keeper 注入），如「轻伤（手）」；「正常」表示清除
            if "condition" in sc:
                cond = (sc.get("condition") or "").strip()
                cond = None if cond in ("", "正常", "无", "无异常") else cond[:50]
                if cond != c.condition:
                    before = c.condition
                    c.condition = cond
                    await self.db.commit()
                    await self.ws.log_event(world_id, "condition_change",
                                            f"{c.name} 状态：{before or '正常'} → {cond or '正常'}",
                                            {"before": before, "after": cond}, actor=c.id, in_world_time=day)
                    applied["conditions"] += 1
            if sc.get("location"):
                loc = await self._resolve_location(world_id, sc["location"])
                if c.current_location_id != loc.id:
                    c.current_location_id = loc.id
                    await self.db.commit()
                    await self.ws.log_event(world_id, "location_move", f"{c.name} 前往 {loc.name}",
                                            {"after": loc.id}, actor=c.id, in_world_time=day)
                    applied["moves"] += 1
            deltas = sc.get("stat_deltas") or {}
            if deltas:
                stats = dict(c.stats or {})
                for k, dv in deltas.items():
                    try:
                        stats[k] = max(0, int(stats.get(k, 0)) + int(dv))
                    except (TypeError, ValueError):
                        continue
                c.stats = stats
                await self.db.commit()
                await self.ws.log_event(world_id, "stat_change", f"{c.name} 数值变化 {deltas}",
                                        {"deltas": deltas, "after": stats}, actor=c.id, in_world_time=day)
                applied["stat_changes"] += 1
            # 死亡：Keeper 显式判定 dead，或 hp 归 0 → 标记阵亡并移出当前场景
            died = sc.get("status") == "dead"
            if not died:
                hp = (c.stats or {}).get("hp")
                try:
                    died = hp is not None and int(hp) <= 0
                except (TypeError, ValueError):
                    died = False
            if died and c.status != "dead":
                c.status = "dead"
                await self.db.execute(delete(SceneParticipant).where(
                    SceneParticipant.scene_id == scene.id, SceneParticipant.character_id == c.id))
                await self.db.commit()
                await self.ws.log_event(world_id, "death", f"{c.name} 阵亡 / 退场",
                                        {"hp": (c.stats or {}).get("hp")}, actor=c.id, in_world_time=day)
                applied["deaths"] += 1
            for it in sc.get("items_gained", []) or []:
                await self.ws.create_item(world_id, {"name": it, "owner_character_id": c.id})
                await self.ws.log_event(world_id, "item_transfer", f"{c.name} 获得 {it}",
                                        {"item": it, "to": c.id}, actor=c.id, in_world_time=day)
                applied["items"] += 1
            for it in sc.get("items_lost", []) or []:
                obj = (await self.db.execute(select(Item).where(
                    Item.world_id == world_id, Item.owner_character_id == c.id, Item.name == it)
                    .limit(1))).scalar_one_or_none()
                if obj:
                    await self.db.execute(delete(Item).where(Item.id == obj.id))
                    await self.db.commit()
                    await self.ws.log_event(world_id, "item_transfer", f"{c.name} 失去 {it}",
                                            {"item": it, "from": c.id}, actor=c.id, in_world_time=day)
                    applied["items"] += 1
        for rc in verdict.get("relationship_changes", []):
            a = by_name.get(rc.get("from", "")); b = by_name.get(rc.get("to", ""))
            if a is None or b is None:
                continue
            existing = (await self.db.execute(select(Relationship).where(
                Relationship.world_id == world_id,
                Relationship.from_character_id == a.id,
                Relationship.to_character_id == b.id).limit(1))).scalar_one_or_none()
            data = {k: rc[k] for k in ("relation_type", "affinity") if rc.get(k) is not None}
            if existing is None:
                await self.ws.create_relationship(world_id, {"from_character_id": a.id, "to_character_id": b.id,
                    "relation_type": rc.get("relation_type", "stranger"), "affinity": int(rc.get("affinity", 0) or 0),
                    "notes": rc.get("reason")})
            else:
                await self.ws.update_relationship(existing.id, data)
            applied["relationships"] += 1
        return applied

    async def _resolve_location(self, world_id, name):
        loc = (await self.db.execute(select(Location).where(
            Location.world_id == world_id, Location.name == name).limit(1))).scalar_one_or_none()
        if loc is None:
            loc = await self.ws.create_location(world_id, {"name": name, "type": "public"})
        return loc

    async def _advance_time(self, world_id):
        world = await self._get(World, world_id)
        cur = world.in_world_time or "第1天"
        nxt = cur
        # 简单天数 +1：识别"第N天"
        import re
        m = re.search(r"第\s*(\d+)\s*天", cur)
        if m:
            n = int(m.group(1)) + 1
            nxt = re.sub(r"第\s*\d+\s*天", f"第{n}天", cur, count=1)
        else:
            nxt = cur + " · 次日"
        if nxt != cur:
            world.in_world_time = nxt
            await self.db.commit()
            await self.ws.log_event(world_id, "time_advance", f"世界时间推进到「{nxt}」",
                                    {"before": cur, "after": nxt}, in_world_time=nxt)
        return nxt

    # ---------------- 一键自动跑本章（若干幕/轮，有上限）----------------
    async def run_chapter(self, world_id, directive: str = ""):
        if await self._active_scene(world_id) is None:
            await self.open_scene(world_id, directive)
        scenes_run, rounds_run = 1, 0
        while scenes_run <= MAX_SCENES_PER_DAY:
            scene_rounds = 0
            scene_ended = False
            while scene_rounds < MAX_ROUNDS_PER_SCENE:
                res = await self.step_round(world_id, directive)
                rounds_run += 1
                scene_rounds += 1
                if res.get("scene_ended"):
                    scene_ended = True
                    break
            if scenes_run >= MAX_SCENES_PER_DAY:
                break
            if scene_ended:
                await self.open_scene(world_id, directive)
                scenes_run += 1
            else:
                break
        return {"success": True, "scenes": scenes_run, "rounds": rounds_run}

    async def _emit_scene_event(self, world_id):
        """为「当前活动场景」补发一个 scene 事件（用于手动 open_scene 后，前端插入新场景块）。"""
        scene = await self._active_scene(world_id)
        if scene is None:
            return None
        p0 = await self.cs.get_participants(scene.id)
        return {"type": "scene", "scene_id": scene.id, "name": scene.name,
                "scenario": scene.scenario, "day_label": scene.day_label,
                "participants": [p.role_name for p in p0]}

    async def run_scene_stream(self, world_id, directive: str = "", max_rounds=MAX_ROUNDS_PER_SCENE):
        """流式版「自动演完本场景」：逐轮流式吐 token，到本幕结束或达上限。"""
        rounds = 0
        while rounds < max_rounds:
            ended = err = False
            async for ev in self.step_round_stream(world_id, directive):
                t = ev.get("type")
                if t == "done":
                    continue                      # 吞掉每轮的 done，最后统一收尾
                if t == "error":
                    err = True
                if t == "judge":
                    ended = bool(ev.get("scene_ended"))
                yield ev
            rounds += 1
            if err or ended:
                break
        yield {"type": "done", "mode": "scene", "rounds": rounds}

    async def run_chapter_stream(self, world_id, directive: str = ""):
        """流式版「自动演完本章」：逐幕逐轮流式吐 token，幕末自动开下一幕，有上限。"""
        scenes_run = 1
        while scenes_run <= MAX_SCENES_PER_DAY:
            scene_rounds = 0
            scene_ended = err = False
            while scene_rounds < MAX_ROUNDS_PER_SCENE:
                ended = False
                async for ev in self.step_round_stream(world_id, directive):
                    t = ev.get("type")
                    if t == "done":
                        continue
                    if t == "error":
                        err = True
                    if t == "judge":
                        ended = bool(ev.get("scene_ended"))
                    yield ev
                scene_rounds += 1
                if err:
                    break
                if ended:
                    scene_ended = True
                    break
            if err or scenes_run >= MAX_SCENES_PER_DAY:
                break
            if scene_ended:
                opened = await self.open_scene(world_id, directive)
                if opened.get("error"):
                    yield {"type": "error", "message": opened["error"]}
                    break
                ev = await self._emit_scene_event(world_id)
                if ev:
                    yield ev
                scenes_run += 1
            else:
                break
        yield {"type": "done", "mode": "chapter", "scenes": scenes_run}

    async def rollback_day(self, world_id):
        return await self.ws.rollback_day(world_id)
