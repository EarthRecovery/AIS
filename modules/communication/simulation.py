"""真实推演引擎：把"世界推进"变成实际跑场景对话 + 每轮世界裁判改状态。

一天 = 一串场景；每个场景跑若干轮对话；每一轮后由世界裁判更新所有在场角色的
记忆/所在地/物品/数值(hp/mp/stamina)/关系/认知；导演决定结束本幕、切下一幕或结束这天。
支持逐步(下一轮/下一幕)与一键自动跑完一天；每天开始拍快照，可回退一天。
"""

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
from storage.models.scene import Scene
from storage.models.scene_message import SceneMessage
from storage.models.scene_participant import SceneParticipant
from storage.models.world import World

MAX_ROUNDS_PER_SCENE = 3
MAX_SCENES_PER_DAY = 3


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
                                      "content": m.content} for m in msgs]
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
        }

    async def scene_messages(self, scene_id):
        """按需拉取某个折叠场景的完整对话。"""
        msgs = await self.cs.get_messages(scene_id)
        return {"messages": [{"speaker_type": m.speaker_type, "speaker_name": m.speaker_name,
                              "content": m.content} for m in msgs]}

    # ---------------- 开场景 ----------------
    async def _day_has_scene(self, world_id, day_label):
        n = (await self.db.execute(
            select(Scene).where(Scene.world_id == world_id, Scene.day_label == day_label)
            .limit(1))).scalar_one_or_none()
        return n is not None

    async def open_scene(self, world_id, directive: str = ""):
        world = await self._get(World, world_id)
        if world is None:
            return {"error": "世界不存在"}
        day = world.in_world_time
        # 这一天的第一幕 → 先拍快照（用于回退一天）
        if not await self._day_has_scene(world_id, day):
            await self.ws._snapshot_world(world_id)
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
                      status="active", day_label=day,
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
                                        {}, actor=ch.id, in_world_time=day)
            self.db.add(SceneParticipant(scene_id=scene.id, role_id=ch.role_id,
                        character_id=ch.id, role_name=nm, display_order=order))
        await self.db.commit()
        await self.ws.log_event(world_id, "scene_open", f"开启场景：{scene.name}",
                                {"scene_id": scene.id}, in_world_time=day)
        return {"scene_id": scene.id, "name": scene.name, "scenario": scene.scenario,
                "participants": plan.get("participants", [])}

    # ---------------- 跑一轮对话 + 世界裁判 ----------------
    async def _speaker_inputs(self, world_id, scene, part):
        """组装某个发言者的 prompt 输入：人格 + 世界观文本 + 感知(含短期/长期记忆)。"""
        wv = await self.cs.get_worldview(scene.worldview_id)
        worldview_text = self.cs._worldview_text(wv)
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
                persona, worldview_text, scene.scenario, roster, transcript, perception):
            text += chunk
        return text.strip()

    async def _run_judge(self, world_id, scene, round_dialogue):
        """世界裁判结算这一轮，返回 (applied, end_scene, end_day)。"""
        chars = await self.ws._all(Character, world_id=world_id)
        by_name = {c.name: c for c in chars}
        ctx, _, _, _ = await self.ws._director_context(world_id)
        parts = await self.cs.get_participants(scene.id)
        char_state = []
        for p in parts:
            c = by_name.get(p.role_name)
            loc = await self._get(Location, c.current_location_id) if c and c.current_location_id else None
            char_state.append({"name": p.role_name, "location": loc.name if loc else None,
                               "stats": (c.stats if c else {}) or {}})
        verdict = await self.llm.keeper_judge_round(ctx, scene.scenario, round_dialogue, char_state)
        applied = await self._apply_verdict(world_id, scene, verdict, by_name)
        sc = verdict.get("scene", {}) or {}
        end_scene = bool(sc.get("should_end"))
        end_day = bool(sc.get("should_end_day"))
        # 剧本节拍达成 → 推进到下一个节拍
        if sc.get("beat_done"):
            await self.ws.advance_beat(world_id)
        if end_scene or end_day:
            scene.status = "ended"
            await self.db.commit()
            # 幕结束 → 给在场角色做记忆沉淀（保留最近 2 幕不沉淀）
            await self._consolidate_participants(world_id, scene)
        if end_day:
            await self._advance_time(world_id)
        return applied, end_scene, end_day

    async def _consolidate_participants(self, world_id, scene):
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

    async def step_round(self, world_id, directive: str = ""):
        """跑一轮：每个在场角色各说一次 → 世界裁判结算状态 → 导演判断幕/天是否结束。"""
        scene = await self._active_scene(world_id)
        if scene is None:
            await self.open_scene(world_id, directive)
            scene = await self._active_scene(world_id)
        if scene is None:
            return {"error": "无法开启场景"}

        parts = await self.cs.get_participants(scene.id)
        roster = await self.cs._build_roster(parts)
        round_dialogue = []
        for p in parts:
            msgs = await self.cs.get_messages(scene.id)
            transcript = self.cs._build_transcript(msgs)
            line = await self._generate_line(world_id, scene, p, roster, transcript)
            if not line:
                continue
            await self.cs.add_message(scene.id, "persona", p.role_name, line, speaker_role_id=p.role_id)
            round_dialogue.append({"speaker": p.role_name, "content": line})

        applied, end_scene, end_day = await self._run_judge(world_id, scene, round_dialogue)
        return {"scene_id": scene.id, "round": round_dialogue, "applied": applied,
                "scene_ended": end_scene or end_day, "day_ended": end_day,
                "active_scene_id": (await self._active_scene(world_id) or scene).id if not (end_scene or end_day) else None}

    async def step_round_stream(self, world_id, directive: str = ""):
        """流式版：逐 token 吐出每个角色的发言，最后吐裁判结算。yields 事件 dict。"""
        scene = await self._active_scene(world_id)
        newly_opened = False
        if scene is None:
            opened = await self.open_scene(world_id, directive)
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
            msgs = await self.cs.get_messages(scene.id)
            transcript = self.cs._build_transcript(msgs)
            persona, worldview_text, perception = await self._speaker_inputs(world_id, scene, p)
            yield {"type": "speaker", "name": p.role_name, "role_id": p.role_id}
            text = ""
            async for chunk in self.llm.group_chat_stream_perceived(
                    persona, worldview_text, scene.scenario, roster, transcript, perception):
                text += chunk
                yield {"type": "token", "text": chunk}
            text = text.strip()
            if text:
                await self.cs.add_message(scene.id, "persona", p.role_name, text, speaker_role_id=p.role_id)
                round_dialogue.append({"speaker": p.role_name, "content": text})
            yield {"type": "speaker_done", "name": p.role_name}

        yield {"type": "judging"}
        applied, end_scene, end_day = await self._run_judge(world_id, scene, round_dialogue)
        yield {"type": "judge", "applied": applied,
               "scene_ended": end_scene or end_day, "day_ended": end_day}
        yield {"type": "done"}

    async def _apply_verdict(self, world_id, scene, verdict, by_name):
        applied = {"memory": 0, "moves": 0, "stat_changes": 0, "items": 0, "relationships": 0, "beliefs": 0}
        day = scene.day_label
        for sc in verdict.get("state_changes", []):
            c = by_name.get(sc.get("character", ""))
            if c is None:
                continue
            if sc.get("memory"):
                await self.ws.add_memory(world_id, c.id, sc["memory"], kind="memory", source_scene_id=scene.id, log=False)
                applied["memory"] += 1
            if sc.get("belief"):
                await self.ws.add_memory(world_id, c.id, sc["belief"], kind="belief", source_scene_id=scene.id, log=False)
                applied["beliefs"] += 1
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

    # ---------------- 一键自动跑完一天 ----------------
    async def run_day(self, world_id, directive: str = ""):
        await self.open_scene(world_id, directive)
        scenes_run, rounds_run = 1, 0
        day_ended = False
        while scenes_run <= MAX_SCENES_PER_DAY and not day_ended:
            scene_rounds = 0
            while scene_rounds < MAX_ROUNDS_PER_SCENE:
                res = await self.step_round(world_id, directive)
                rounds_run += 1
                scene_rounds += 1
                if res.get("day_ended"):
                    day_ended = True
                    break
                if res.get("scene_ended"):
                    break
            if day_ended:
                break
            if scenes_run < MAX_SCENES_PER_DAY:
                await self.open_scene(world_id, directive)
                scenes_run += 1
            else:
                break
        if not day_ended:
            await self._advance_time(world_id)
            # 收尾：结束仍开着的场景
            cur = await self._active_scene(world_id)
            if cur:
                cur.status = "ended"
                await self.db.commit()
        return {"success": True, "scenes": scenes_run, "rounds": rounds_run}

    async def rollback_day(self, world_id):
        return await self.ws.rollback_day(world_id)
