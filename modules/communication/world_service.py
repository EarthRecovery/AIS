"""持久世界的读写编排：对 World 及其所有从属实体做 CRUD，

并在「语义性状态变更」(关系/物品易主/心智/认知/世界观/时间) 时追加一条
WorldEvent(含 before/after)，落实「可变当前态 + 追加事件日志」架构。
"""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.clients.llm_client import LLMClient
from modules.deps import get_llm_client
from storage.db import get_db
from storage.models.ability import Ability
from storage.models.agent_memory import AgentMemory
from storage.models.character import Character
from storage.models.common_knowledge import CommonKnowledge
from storage.models.item import Item
from storage.models.location import Location
from storage.models.mental_state import MentalState
from storage.models.relationship import Relationship
from storage.models.scene import Scene
from storage.models.scene_knowledge import SceneKnowledge
from storage.models.scene_message import SceneMessage
from storage.models.scene_participant import SceneParticipant
from storage.models.world import World
from storage.models.world_event import WorldEvent
from storage.models.world_snapshot import WorldSnapshot
from storage.models.worldview import Worldview


def _apply(obj, data: dict):
    """把请求里非 None 的字段写到 ORM 对象上。"""
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)


class WorldService:
    def __init__(self, llm: LLMClient = Depends(get_llm_client), db: AsyncSession = Depends(get_db)):
        self.llm = llm
        self.db = db

    async def _get(self, model, id_):
        res = await self.db.execute(select(model).where(model.id == id_))
        return res.scalar_one_or_none()

    async def _all(self, model, **filters):
        stmt = select(model)
        for k, v in filters.items():
            stmt = stmt.where(getattr(model, k) == v)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def _save(self, obj):
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def log_event(self, world_id, kind, summary, payload=None, actor=None, in_world_time=None):
        ev = WorldEvent(
            world_id=world_id, kind=kind, summary=summary,
            payload=payload or {}, actor_character_id=actor, in_world_time=in_world_time,
        )
        return await self._save(ev)

    async def _world_time(self, world_id) -> Optional[str]:
        w = await self._get(World, world_id)
        return w.in_world_time if w else None

    # ============ World ============
    async def create_world(self, user_id, name, worldview_id=None) -> World:
        return await self._save(World(user_id=user_id, name=name, worldview_id=worldview_id))

    async def list_worlds(self, user_id) -> List[World]:
        res = await self.db.execute(
            select(World).where(World.user_id == user_id).order_by(World.id.desc())
        )
        return res.scalars().all()

    async def update_world(self, world_id, data: dict) -> Optional[World]:
        w = await self._get(World, world_id)
        if not w:
            return None
        before_time = w.in_world_time
        before_wv = w.worldview_id
        _apply(w, data)
        await self.db.commit()
        await self.db.refresh(w)
        if data.get("in_world_time") and data["in_world_time"] != before_time:
            await self.log_event(world_id, "time_advance", f"世界时间推进到「{w.in_world_time}」",
                                  {"before": before_time, "after": w.in_world_time}, in_world_time=w.in_world_time)
        if data.get("worldview_id") and data["worldview_id"] != before_wv:
            await self.log_event(world_id, "worldview_change", "切换当前世界观",
                                 {"before": before_wv, "after": w.worldview_id}, in_world_time=w.in_world_time)
        return w

    async def delete_world(self, world_id) -> bool:
        for model in (WorldEvent, AgentMemory, CommonKnowledge, Ability, MentalState,
                      Relationship, Item, Location, Character):
            await self.db.execute(delete(model).where(model.world_id == world_id)
                                  if hasattr(model, "world_id")
                                  else delete(model).where(model.character_id.in_(
                                      select(Character.id).where(Character.world_id == world_id))))
        await self.db.execute(delete(World).where(World.id == world_id))
        await self.db.commit()
        return True

    # ============ Worldview（更改世界观） ============
    async def update_worldview(self, worldview_id, data: dict, world_id=None):
        wv = await self._get(Worldview, worldview_id)
        if not wv:
            return None
        _apply(wv, data)
        await self.db.commit()
        await self.db.refresh(wv)
        if world_id:
            await self.log_event(world_id, "worldview_change", f"修改世界观「{wv.name}」",
                                 {"worldview_id": worldview_id, "after": data},
                                 in_world_time=await self._world_time(world_id))
        return wv

    # ============ Character ============
    DEFAULT_STATS = {"hp": 100, "mp": 100, "stamina": 100}

    async def create_character(self, world_id, name, role_id=None, status=None, stats=None) -> Character:
        c = Character(world_id=world_id, name=name, role_id=role_id, status=status or "active",
                      stats=dict(stats) if stats else dict(self.DEFAULT_STATS))
        return await self._save(c)

    async def update_character(self, char_id, data: dict):
        c = await self._get(Character, char_id)
        if not c:
            return None
        before_loc = c.current_location_id
        _apply(c, data)
        await self.db.commit()
        await self.db.refresh(c)
        if data.get("current_location_id") and data["current_location_id"] != before_loc:
            await self.log_event(c.world_id, "location_move", f"{c.name} 移动了位置",
                                 {"before": before_loc, "after": c.current_location_id}, actor=c.id,
                                 in_world_time=await self._world_time(c.world_id))
        return c

    async def delete_character(self, char_id) -> bool:
        c = await self._get(Character, char_id)
        if not c:
            return False
        await self.db.execute(delete(Ability).where(Ability.character_id == char_id))
        await self.db.execute(delete(MentalState).where(MentalState.character_id == char_id))
        await self.db.execute(delete(AgentMemory).where(AgentMemory.character_id == char_id))
        await self.db.execute(delete(Character).where(Character.id == char_id))
        await self.db.commit()
        return True

    # ---- MentalState（每角色一条当前态，upsert）----
    async def get_mental(self, char_id):
        res = await self.db.execute(select(MentalState).where(MentalState.character_id == char_id))
        return res.scalar_one_or_none()

    async def upsert_mental(self, char_id, data: dict):
        ms = await self.get_mental(char_id)
        if ms is None:
            ms = MentalState(character_id=char_id)
            self.db.add(ms)
        _apply(ms, data)
        await self.db.commit()
        await self.db.refresh(ms)
        c = await self._get(Character, char_id)
        if c:
            await self.log_event(c.world_id, "mental_update", f"{c.name} 的心智状态更新",
                                 {"character_id": char_id, "after": data}, actor=char_id,
                                 in_world_time=await self._world_time(c.world_id))
        return ms

    # ---- Ability ----
    async def create_ability(self, char_id, name, description=None, level=None):
        return await self._save(Ability(character_id=char_id, name=name,
                                        description=description, level=level or 1))

    async def update_ability(self, ability_id, data: dict):
        ab = await self._get(Ability, ability_id)
        if not ab:
            return None
        _apply(ab, data)
        await self.db.commit()
        await self.db.refresh(ab)
        return ab

    async def delete_ability(self, ability_id):
        await self.db.execute(delete(Ability).where(Ability.id == ability_id))
        await self.db.commit()
        return True

    # ---- Belief / AgentMemory（角色私有记忆，belief 为其中一种 kind）----
    async def create_belief(self, world_id, data: dict):
        d = dict(data)
        holder = d.pop("holder_character_id", None)
        return await self._save(AgentMemory(
            world_id=world_id, character_id=holder, kind="belief",
            **{k: v for k, v in d.items() if v is not None}))

    async def update_belief(self, belief_id, data: dict):
        b = await self._get(AgentMemory, belief_id)
        if not b:
            return None
        _apply(b, data)
        await self.db.commit()
        await self.db.refresh(b)
        await self.log_event(b.world_id, "belief_update", "认知更新",
                             {"memory_id": belief_id, "after": data},
                             actor=b.character_id, in_world_time=await self._world_time(b.world_id))
        return b

    async def delete_belief(self, belief_id):
        await self.db.execute(delete(AgentMemory).where(AgentMemory.id == belief_id))
        await self.db.commit()
        return True

    # ---- AgentMemory（通用：记忆/事实/观察等任意 kind）----
    async def add_memory(self, world_id, character_id, content, kind="memory",
                         source_scene_id=None, importance=0, log=True):
        m = await self._save(AgentMemory(
            world_id=world_id, character_id=character_id, kind=kind,
            content=content, source_scene_id=source_scene_id, importance=importance))
        if log:
            await self.log_event(world_id, "memory_write", f"角色 #{character_id} 记住了一条 {kind}",
                                 {"memory_id": m.id, "content": content[:120]},
                                 actor=character_id, in_world_time=await self._world_time(world_id))
        return m

    async def list_memories(self, character_id):
        res = await self.db.execute(
            select(AgentMemory).where(AgentMemory.character_id == character_id)
            .order_by(AgentMemory.id.desc()))
        return res.scalars().all()

    async def delete_memory(self, memory_id):
        await self.db.execute(delete(AgentMemory).where(AgentMemory.id == memory_id))
        await self.db.commit()
        return True

    # ---- CommonKnowledge（世界常识，所有 agent 可见）----
    async def add_common_knowledge(self, world_id, content):
        return await self._save(CommonKnowledge(world_id=world_id, content=content))

    async def list_common_knowledge(self, world_id):
        res = await self.db.execute(
            select(CommonKnowledge).where(CommonKnowledge.world_id == world_id)
            .order_by(CommonKnowledge.id.desc()))
        return res.scalars().all()

    async def delete_common_knowledge(self, ck_id):
        await self.db.execute(delete(CommonKnowledge).where(CommonKnowledge.id == ck_id))
        await self.db.commit()
        return True

    # ---- SceneKnowledge（场景知识，在场 agent 可获知）----
    async def add_scene_knowledge(self, scene_id, content, scope="public"):
        return await self._save(SceneKnowledge(scene_id=scene_id, content=content, scope=scope))

    async def list_scene_knowledge(self, scene_id):
        res = await self.db.execute(
            select(SceneKnowledge).where(SceneKnowledge.scene_id == scene_id)
            .order_by(SceneKnowledge.id.desc()))
        return res.scalars().all()

    async def delete_scene_knowledge(self, sk_id):
        await self.db.execute(delete(SceneKnowledge).where(SceneKnowledge.id == sk_id))
        await self.db.commit()
        return True

    # ---- 感知视图：喂给某 agent 的、它"该知道"的信息 ----
    async def build_perception(self, world_id, character_id, scene_id=None,
                               recent_scenes=3, short_cap=10, long_cap=8):
        """构造某角色的感知切片：世界常识 + 短期记忆(最近几个场景) + 长期记忆(重要的事)
        + 自我认知 + 当前场景知识。

        短期记忆：最近 recent_scenes 个场景里发生的记忆（最多 short_cap 条）。
        长期记忆：重要度较高(importance>=2)、且不在短期里的记忆（按重要度，最多 long_cap 条）。
        """
        commons = await self.list_common_knowledge(world_id)
        all_mem = await self.list_memories(character_id)  # 按 id 倒序（新→旧）
        scene_k = await self.list_scene_knowledge(scene_id) if scene_id else []
        mental = await self.get_mental(character_id)

        # 最近几个场景的 id 集合（按记忆里出现的 source_scene_id，取最近 recent_scenes 个）
        recent_sids, seen = [], set()
        for m in all_mem:
            sid = m.source_scene_id
            if sid and sid not in seen:
                seen.add(sid)
                recent_sids.append(sid)
            if len(recent_sids) >= recent_scenes:
                break
        recent_set = set(recent_sids)

        short, long = [], []
        for m in all_mem:
            in_recent = (m.source_scene_id in recent_set) if m.source_scene_id else False
            if in_recent and len(short) < short_cap:
                short.append(m)
            elif (m.importance or 0) >= 2 and not m.consolidated and len(long) < long_cap:
                # 已沉淀进 self_summary 的不再单独注入，避免重复且让长期记忆有界
                long.append(m)
        # 长期按重要度排序
        long.sort(key=lambda m: (-(m.importance or 0), -m.id))

        def ser(m):
            return {"kind": m.kind, "content": m.content, "confidence": m.confidence}

        return {
            "common_knowledge": [c.content for c in commons],
            "self_summary": (mental.self_summary if mental else None),
            "short_term": [ser(m) for m in short],
            "long_term": [ser(m) for m in long],
            "scene_knowledge": [s.content for s in scene_k],
        }

    async def character_detail(self, world_id, char_id):
        """单个角色的详细信息 + 短期/长期记忆（给前端角色详情面板）。"""
        c = await self._get(Character, char_id)
        if c is None:
            return None
        loc = await self._get(Location, c.current_location_id) if c.current_location_id else None
        ms = await self.get_mental(char_id)
        abilities = await self._all(Ability, character_id=char_id)
        items = (await self.db.execute(select(Item).where(
            Item.world_id == world_id, Item.owner_character_id == char_id))).scalars().all()
        chars = await self._all(Character, world_id=world_id)
        name_of = {x.id: x.name for x in chars}
        rels = (await self.db.execute(select(Relationship).where(
            Relationship.world_id == world_id, Relationship.from_character_id == char_id))).scalars().all()
        perc = await self.build_perception(world_id, char_id, None)
        return {
            "id": c.id, "name": c.name, "status": c.status,
            "location": loc.name if loc else None, "stats": c.stats or {},
            "mental": (None if ms is None else {
                "mood": ms.mood, "goals": ms.goals, "motivation": ms.motivation,
                "self_summary": ms.self_summary}),
            "abilities": [{"name": a.name, "level": a.level, "description": a.description} for a in abilities],
            "items": [{"name": i.name, "description": i.description} for i in items],
            "relationships": [{"to": name_of.get(r.to_character_id, f"#{r.to_character_id}"),
                               "relation_type": r.relation_type, "affinity": r.affinity,
                               "notes": r.notes} for r in rels],
            "short_term": perc.get("short_term", []),
            "long_term": perc.get("long_term", []),
        }

    # ---- 角色按名查找（Keeper 把名字解析回 character_id）----
    async def character_by_name(self, world_id, name):
        res = await self.db.execute(
            select(Character).where(Character.world_id == world_id, Character.name == name))
        return res.scalars().first()

    async def world_common_texts(self, world_id):
        """世界级公共可见信息：世界观散文 + 常识条目。"""
        texts = []
        w = await self._get(World, world_id)
        if w and w.worldview_id:
            wv = await self._get(Worldview, w.worldview_id)
            if wv:
                if wv.description:
                    texts.append(wv.description.strip())
                if wv.rules:
                    texts.append("【世界规则】" + wv.rules.strip())
        for c in await self.list_common_knowledge(world_id):
            texts.append(c.content)
        return texts

    # ---- Keeper：消化场景 → 写各角色记忆 + 决定场景切换 ----
    async def keeper_digest_scene(self, scene_id):
        scene = await self._get(Scene, scene_id)
        if scene is None or not scene.world_id:
            return {"error": "需要一个属于某世界的场景"}
        world_id = scene.world_id

        common = await self.world_common_texts(world_id)
        parts = (await self.db.execute(
            select(SceneParticipant).where(SceneParticipant.scene_id == scene_id))).scalars().all()
        participant_names = [p.role_name for p in parts]
        msgs = (await self.db.execute(
            select(SceneMessage).where(SceneMessage.scene_id == scene_id)
            .order_by(SceneMessage.timestamp, SceneMessage.id))).scalars().all()
        transcript = [{"speaker_name": m.speaker_name, "content": m.content} for m in msgs]

        digest = await self.llm.keeper_digest(common, scene.scenario, participant_names, transcript)

        # 1) 写各角色记忆
        written = 0
        for mem in digest.get("memories", []):
            ch = await self.character_by_name(world_id, mem.get("character", ""))
            if ch is None:
                continue
            await self.add_memory(world_id, ch.id, mem.get("content", ""),
                                  kind=mem.get("kind", "memory"), source_scene_id=scene_id,
                                  importance=int(mem.get("importance", 0) or 0), log=False)
            written += 1

        # 2) 场景切换决策
        scene_decision = digest.get("scene", {}) or {}
        next_scene_id = None
        if scene_decision.get("should_switch"):
            scene.status = "ended"
            scene.ended_at = func.now()
            await self.db.commit()
            nxt = scene_decision.get("next", {}) or {}
            new_scene = Scene(user_id=scene.user_id, world_id=world_id,
                              worldview_id=scene.worldview_id,
                              name=nxt.get("name", "新场景"), scenario=nxt.get("setting", ""),
                              prev_scene_id=scene_id)
            new_scene = await self._save(new_scene)
            for order, nm in enumerate(nxt.get("participants", []) or []):
                ch = await self.character_by_name(world_id, nm)
                self.db.add(SceneParticipant(
                    scene_id=new_scene.id, role_id=(ch.role_id if ch else None),
                    character_id=(ch.id if ch else None), role_name=nm, display_order=order))
            await self.db.commit()
            next_scene_id = new_scene.id
            await self.log_event(world_id, "scene_change",
                                 f"场景切换：{scene.name} → {new_scene.name}",
                                 {"from": scene_id, "to": next_scene_id,
                                  "reason": scene_decision.get("reason", "")},
                                 in_world_time=await self._world_time(world_id))

        await self.log_event(world_id, "keeper_digest",
                             f"记录官消化场景「{scene.name}」，写入 {written} 条记忆",
                             {"scene_id": scene_id, "memories_written": written,
                              "switched": bool(next_scene_id)},
                             in_world_time=await self._world_time(world_id))
        return {"memories_written": written, "switched": bool(next_scene_id),
                "next_scene_id": next_scene_id, "decision": scene_decision}

    # ============ Location ============
    async def create_location(self, world_id, data: dict):
        return await self._save(Location(world_id=world_id, **{k: v for k, v in data.items() if v is not None}))

    async def update_location(self, loc_id, data: dict):
        loc = await self._get(Location, loc_id)
        if not loc:
            return None
        _apply(loc, data)
        await self.db.commit()
        await self.db.refresh(loc)
        return loc

    async def delete_location(self, loc_id):
        await self.db.execute(delete(Location).where(Location.id == loc_id))
        await self.db.commit()
        return True

    # ============ Item ============
    async def create_item(self, world_id, data: dict):
        return await self._save(Item(world_id=world_id, **{k: v for k, v in data.items() if v is not None}))

    async def update_item(self, item_id, data: dict):
        it = await self._get(Item, item_id)
        if not it:
            return None
        before_owner = it.owner_character_id
        _apply(it, data)
        await self.db.commit()
        await self.db.refresh(it)
        if "owner_character_id" in data and data["owner_character_id"] != before_owner:
            await self.log_event(it.world_id, "item_transfer", f"物品「{it.name}」易主",
                                 {"item_id": item_id, "before": before_owner, "after": it.owner_character_id},
                                 in_world_time=await self._world_time(it.world_id))
        return it

    async def delete_item(self, item_id):
        await self.db.execute(delete(Item).where(Item.id == item_id))
        await self.db.commit()
        return True

    # ============ Relationship ============
    async def create_relationship(self, world_id, data: dict):
        return await self._save(Relationship(world_id=world_id, **{k: v for k, v in data.items() if v is not None}))

    async def update_relationship(self, rel_id, data: dict):
        rel = await self._get(Relationship, rel_id)
        if not rel:
            return None
        before = {"affinity": rel.affinity, "relation_type": rel.relation_type}
        _apply(rel, data)
        await self.db.commit()
        await self.db.refresh(rel)
        if ("affinity" in data or "relation_type" in data):
            await self.log_event(rel.world_id, "relationship_change", "关系变化",
                                 {"rel_id": rel_id, "before": before,
                                  "after": {"affinity": rel.affinity, "relation_type": rel.relation_type}},
                                 actor=rel.from_character_id, in_world_time=await self._world_time(rel.world_id))
        return rel

    async def delete_relationship(self, rel_id):
        await self.db.execute(delete(Relationship).where(Relationship.id == rel_id))
        await self.db.commit()
        return True

    # ============ 读取 ============
    async def get_events(self, world_id, limit=100):
        res = await self.db.execute(
            select(WorldEvent).where(WorldEvent.world_id == world_id)
            .order_by(WorldEvent.id.desc()).limit(limit)
        )
        return res.scalars().all()

    async def list_worldviews(self, user_id):
        res = await self.db.execute(
            select(Worldview).where(Worldview.user_id == user_id).order_by(Worldview.id.desc())
        )
        return res.scalars().all()

    async def world_detail(self, world_id):
        """一次性返回世界全貌，供前端管理页加载。"""
        world = await self._get(World, world_id)
        if not world:
            return None
        worldview = await self._get(Worldview, world.worldview_id) if world.worldview_id else None
        characters = await self._all(Character, world_id=world_id)
        char_blocks = []
        for c in characters:
            mental = await self.get_mental(c.id)
            abilities = await self._all(Ability, character_id=c.id)
            memories = (await self.db.execute(
                select(AgentMemory).where(AgentMemory.character_id == c.id)
                .order_by(AgentMemory.id.desc()))).scalars().all()
            beliefs = [m for m in memories if m.kind == "belief"]
            char_blocks.append({"character": c, "mental": mental, "abilities": abilities,
                                "beliefs": beliefs, "memories": memories})
        locations = await self._all(Location, world_id=world_id)
        items = await self._all(Item, world_id=world_id)
        relationships = await self._all(Relationship, world_id=world_id)
        return {
            "world": world, "worldview": worldview, "characters": char_blocks,
            "locations": locations, "items": items, "relationships": relationships,
        }

    # ============ 每日结算：世界推演引擎 ============
    async def _director_context(self, world_id):
        """给世界导演的输入：世界观(含背景) + 常识 + 角色摘要 + 关系 + 近期事件 + 时间。"""
        world = await self._get(World, world_id)
        wv = await self._get(Worldview, world.worldview_id) if world and world.worldview_id else None
        chars = await self._all(Character, world_id=world_id)
        char_ctx = []
        for c in chars:
            ms = await self.get_mental(c.id)
            mems = (await self.db.execute(
                select(AgentMemory).where(AgentMemory.character_id == c.id)
                .order_by(AgentMemory.id.desc()).limit(4))).scalars().all()
            bits = []
            if ms and ms.self_summary:
                bits.append(ms.self_summary)
            if ms and ms.mood:
                bits.append(f"心情:{ms.mood}")
            if ms and ms.goals:
                bits.append(f"目标:{ms.goals}")
            bits += [m.content for m in mems]
            char_ctx.append({"name": c.name, "summary": "；".join(b for b in bits if b)})
        rels = []
        for r in await self._all(Relationship, world_id=world_id):
            fn = next((c.name for c in chars if c.id == r.from_character_id), f"#{r.from_character_id}")
            tn = next((c.name for c in chars if c.id == r.to_character_id), f"#{r.to_character_id}")
            rels.append({"from": fn, "to": tn, "relation_type": r.relation_type, "affinity": r.affinity})
        commons = [c.content for c in await self.list_common_knowledge(world_id)]
        recent = [f"{e.in_world_time or ''} {e.summary}" for e in (await self.get_events(world_id, limit=12))]
        return {
            "worldview": ({"description": wv.description, "rules": wv.rules,
                           "background": wv.background} if wv else {}),
            "characters": char_ctx, "relationships": rels,
            "common_knowledge": commons, "recent_events": recent,
            "in_world_time": world.in_world_time if world else "",
            "beat": self._current_beat(world),
        }, world, wv, chars

    # ---- 剧本大纲 / 节拍 ----
    @staticmethod
    def _current_beat(world):
        outline = (world.outline or []) if world else []
        idx = world.beat_index if world else 0
        if outline and 0 <= idx < len(outline):
            return outline[idx]
        return None

    async def generate_outline(self, world_id, directive=""):
        ctx, world, _, _ = await self._director_context(world_id)
        beats = await self.llm.keeper_write_outline(ctx, directive)
        if world is not None:
            world.outline = beats
            world.beat_index = 0
            await self.db.commit()
            await self.log_event(world_id, "outline_set", f"生成剧本大纲（{len(beats)} 个节拍）",
                                 {"beats": [b.get("title") for b in beats]},
                                 in_world_time=world.in_world_time)
        return beats

    async def advance_beat(self, world_id):
        world = await self._get(World, world_id)
        if world is None or not world.outline:
            return None
        if world.beat_index < len(world.outline) - 1:
            world.beat_index += 1
            await self.db.commit()
            cur = self._current_beat(world)
            await self.log_event(world_id, "beat_advance",
                                 f"剧情推进到节拍：{cur.get('title') if cur else ''}",
                                 {"beat_index": world.beat_index}, in_world_time=world.in_world_time)
            return cur
        return None

    # ---- 记忆沉淀：把旧的零散记忆压进角色的长期自我认知 ----
    async def consolidate_character(self, character_id, keep_scene_ids, threshold=8):
        c = await self._get(Character, character_id)
        if c is None:
            return False
        res = await self.db.execute(
            select(AgentMemory).where(AgentMemory.character_id == character_id,
                                      AgentMemory.consolidated == False)  # noqa: E712
            .order_by(AgentMemory.id))
        mems = res.scalars().all()
        keep = set(keep_scene_ids or [])
        older = [m for m in mems if (m.source_scene_id not in keep)]
        if len(older) < threshold:
            return False
        ms = await self.get_mental(character_id)
        cur_summary = ms.self_summary if ms else ""
        new_summary = await self.llm.keeper_consolidate(c.name, cur_summary, [m.content for m in older])
        # 直接写 self_summary（不走 upsert_mental，避免刷一堆 mental_update 事件）
        if ms is None:
            ms = MentalState(character_id=character_id)
            self.db.add(ms)
        ms.self_summary = new_summary
        for m in older:
            m.consolidated = True
        await self.db.commit()
        await self.log_event(c.world_id, "memory_consolidate",
                             f"{c.name} 把 {len(older)} 条旧记忆沉淀进长期记忆",
                             {"count": len(older)}, actor=character_id,
                             in_world_time=await self._world_time(c.world_id))
        return True

    @staticmethod
    def _row(obj, fields):
        return {f: getattr(obj, f) for f in fields}

    # 各表参与快照的字段（不含时间戳，回退时让其重置）
    _SNAP_FIELDS = {
        "character": ["id", "world_id", "role_id", "name", "status", "current_location_id", "stats"],
        "mental_state": ["id", "character_id", "mood", "goals", "motivation", "self_summary"],
        "agent_memory": ["id", "world_id", "character_id", "kind", "content", "subject_type",
                         "subject_id", "confidence", "is_true", "source_scene_id", "importance"],
        "relationship": ["id", "world_id", "from_character_id", "to_character_id",
                         "relation_type", "affinity", "notes"],
        "item": ["id", "world_id", "name", "description", "owner_character_id", "location_id", "state"],
        "location": ["id", "world_id", "name", "type", "description", "parent_location_id"],
        "ability": ["id", "character_id", "name", "description", "level"],
        "common_knowledge": ["id", "world_id", "content"],
        "scene": ["id", "user_id", "world_id", "worldview_id", "name", "scenario", "summary",
                  "status", "prev_scene_id", "day_label"],
        "scene_participant": ["id", "scene_id", "role_id", "character_id", "role_name", "display_order"],
        "scene_message": ["id", "scene_id", "speaker_type", "speaker_role_id", "speaker_name", "content"],
    }

    async def _snapshot_world(self, world_id):
        """结算前给世界拍一张全量快照，存入 ais_world_snapshots。"""
        world = await self._get(World, world_id)
        wv = await self._get(Worldview, world.worldview_id) if world and world.worldview_id else None
        chars = await self._all(Character, world_id=world_id)
        char_ids = [c.id for c in chars]

        async def rows(model, key, **flt):
            objs = (await self.db.execute(
                select(model).where(*[getattr(model, k) == v for k, v in flt.items()]))).scalars().all()
            return [self._row(o, self._SNAP_FIELDS[key]) for o in objs]

        mentals, abilities = [], []
        if char_ids:
            ms = (await self.db.execute(
                select(MentalState).where(MentalState.character_id.in_(char_ids)))).scalars().all()
            mentals = [self._row(o, self._SNAP_FIELDS["mental_state"]) for o in ms]
            ab = (await self.db.execute(
                select(Ability).where(Ability.character_id.in_(char_ids)))).scalars().all()
            abilities = [self._row(o, self._SNAP_FIELDS["ability"]) for o in ab]

        max_event = (await self.db.execute(
            select(func.max(WorldEvent.id)).where(WorldEvent.world_id == world_id))).scalar() or 0

        state = {
            "world": {"in_world_time": world.in_world_time, "worldview_id": world.worldview_id,
                      "status": world.status, "beat_index": world.beat_index, "outline": world.outline},
            "worldview": (self._row(wv, ["id", "description", "rules", "background"]) if wv else None),
            "characters": [self._row(c, self._SNAP_FIELDS["character"]) for c in chars],
            "mental_states": mentals,
            "abilities": abilities,
            "agent_memories": await rows(AgentMemory, "agent_memory", world_id=world_id),
            "relationships": await rows(Relationship, "relationship", world_id=world_id),
            "items": await rows(Item, "item", world_id=world_id),
            "locations": await rows(Location, "location", world_id=world_id),
            "common_knowledge": await rows(CommonKnowledge, "common_knowledge", world_id=world_id),
            "scenes": await rows(Scene, "scene", world_id=world_id),
            "events_max_id": int(max_event),
        }
        # 场景对话（参与者 + 消息）按本世界的场景集合捕获
        scene_ids = [s["id"] for s in state["scenes"]]
        sp, sm = [], []
        if scene_ids:
            sp_objs = (await self.db.execute(
                select(SceneParticipant).where(SceneParticipant.scene_id.in_(scene_ids)))).scalars().all()
            sp = [self._row(o, self._SNAP_FIELDS["scene_participant"]) for o in sp_objs]
            sm_objs = (await self.db.execute(
                select(SceneMessage).where(SceneMessage.scene_id.in_(scene_ids)))).scalars().all()
            sm = [self._row(o, self._SNAP_FIELDS["scene_message"]) for o in sm_objs]
        state["scene_participants"] = sp
        state["scene_messages"] = sm
        snap = WorldSnapshot(world_id=world_id, day_label=world.in_world_time, state=state)
        return await self._save(snap)

    async def has_snapshot(self, world_id):
        res = await self.db.execute(
            select(func.count(WorldSnapshot.id)).where(WorldSnapshot.world_id == world_id))
        return (res.scalar() or 0) > 0

    async def rollback_day(self, world_id):
        """回退一天：恢复最近一张快照，并删除该快照之后产生的事件与快照。"""
        res = await self.db.execute(
            select(WorldSnapshot).where(WorldSnapshot.world_id == world_id)
            .order_by(WorldSnapshot.id.desc()).limit(1))
        snap = res.scalar_one_or_none()
        if snap is None:
            return {"success": False, "error": "没有可回退的快照"}
        st = snap.state or {}

        # 1) 删除该世界的所有子表行（mental/ability/场景对话 先按当前关联删）
        chars_now = await self._all(Character, world_id=world_id)
        cids = [c.id for c in chars_now]
        if cids:
            await self.db.execute(delete(MentalState).where(MentalState.character_id.in_(cids)))
            await self.db.execute(delete(Ability).where(Ability.character_id.in_(cids)))
        scenes_now = await self._all(Scene, world_id=world_id)
        sids = [s.id for s in scenes_now]
        if sids:
            await self.db.execute(delete(SceneParticipant).where(SceneParticipant.scene_id.in_(sids)))
            await self.db.execute(delete(SceneMessage).where(SceneMessage.scene_id.in_(sids)))
        for model in (AgentMemory, Relationship, Item, Location, CommonKnowledge, Scene, Character):
            await self.db.execute(delete(model).where(model.world_id == world_id))

        # 2) 按快照重建（保留原 id，维持彼此引用）
        def mk(model, rows):
            for r in rows or []:
                self.db.add(model(**r))
        mk(Character, st.get("characters"))
        mk(MentalState, st.get("mental_states"))
        mk(Ability, st.get("abilities"))
        mk(AgentMemory, st.get("agent_memories"))
        mk(Relationship, st.get("relationships"))
        mk(Item, st.get("items"))
        mk(Location, st.get("locations"))
        mk(CommonKnowledge, st.get("common_knowledge"))
        mk(Scene, st.get("scenes"))
        mk(SceneParticipant, st.get("scene_participants"))
        mk(SceneMessage, st.get("scene_messages"))

        # 3) 恢复世界与世界观标量字段
        world = await self._get(World, world_id)
        w = st.get("world") or {}
        if world:
            world.in_world_time = w.get("in_world_time", world.in_world_time)
            world.worldview_id = w.get("worldview_id", world.worldview_id)
            world.status = w.get("status", world.status)
            if "beat_index" in w:
                world.beat_index = w.get("beat_index") or 0
            if "outline" in w:
                world.outline = w.get("outline")
        wv_snap = st.get("worldview")
        if wv_snap:
            wv = await self._get(Worldview, wv_snap["id"])
            if wv:
                wv.description = wv_snap.get("description")
                wv.rules = wv_snap.get("rules")
                wv.background = wv_snap.get("background")

        # 4) 删除快照之后产生的事件 + 这张快照
        await self.db.execute(delete(WorldEvent).where(
            WorldEvent.world_id == world_id, WorldEvent.id > int(st.get("events_max_id", 0))))
        await self.db.execute(delete(WorldSnapshot).where(WorldSnapshot.id == snap.id))
        await self.db.commit()
        return {"success": True, "restored_to": snap.day_label}

    async def advance_day(self, world_id, directive: str = ""):
        """每日结算：拍快照 → 世界导演推演一天 → 应用全部变化（全量自主）。"""
        world = await self._get(World, world_id)
        if world is None:
            return {"success": False, "error": "世界不存在"}

        await self._snapshot_world(world_id)
        ctx, world, wv, chars = await self._director_context(world_id)
        plan = await self.llm.keeper_direct_day(ctx, directive)

        t_next = plan.get("next_time") or world.in_world_time
        name_to_char = {c.name: c for c in chars}

        async def ensure_char(name):
            if name in name_to_char:
                return name_to_char[name]
            return None

        applied = {"events": 0, "memories": 0, "relationship_changes": 0,
                   "new_characters": 0, "common_knowledge": 0, "scene_switched": False,
                   "background_appended": False}

        # 当日叙事
        day_summary = (plan.get("day_summary") or "").strip()
        if day_summary:
            await self.log_event(world_id, "day_summary", day_summary,
                                 {"directive": directive}, in_world_time=t_next)

        # 剧情事件
        for ev in plan.get("events", []):
            if ev.get("summary"):
                await self.log_event(world_id, ev.get("kind", "plot"), ev["summary"],
                                     {}, in_world_time=t_next)
                applied["events"] += 1

        # 新角色（不建 Role，纯世界角色 + 自我摘要，回退可净删）
        for nc in plan.get("new_characters", []):
            nm = (nc.get("name") or "").strip()
            if not nm or nm in name_to_char:
                continue
            ch = await self.create_character(world_id, nm)
            name_to_char[nm] = ch
            desc = nc.get("description") or ""
            traits = "、".join(nc.get("personality", []) or [])
            await self.upsert_mental(ch.id, {"self_summary": desc, "motivation": traits})
            await self.log_event(world_id, "character_spawn", f"新角色登场：{nm}",
                                 {"description": desc}, actor=ch.id, in_world_time=t_next)
            applied["new_characters"] += 1

        # 记忆
        for m in plan.get("memories", []):
            ch = name_to_char.get(m.get("character", ""))
            if ch is None or not m.get("content"):
                continue
            await self.add_memory(world_id, ch.id, m["content"], kind=m.get("kind", "memory"),
                                  importance=int(m.get("importance", 0) or 0), log=False)
            applied["memories"] += 1

        # 关系变化（按名找/建，落库并记事件）
        for rc in plan.get("relationship_changes", []):
            a = name_to_char.get(rc.get("from", "")); b = name_to_char.get(rc.get("to", ""))
            if a is None or b is None:
                continue
            res = await self.db.execute(select(Relationship).where(
                Relationship.world_id == world_id,
                Relationship.from_character_id == a.id, Relationship.to_character_id == b.id))
            rel = res.scalar_one_or_none()
            data = {k: rc[k] for k in ("relation_type", "affinity") if rc.get(k) is not None}
            if rel is None:
                await self.create_relationship(world_id, {
                    "from_character_id": a.id, "to_character_id": b.id,
                    "relation_type": rc.get("relation_type", "stranger"),
                    "affinity": int(rc.get("affinity", 0) or 0), "notes": rc.get("reason")})
            else:
                await self.update_relationship(rel.id, data)
            applied["relationship_changes"] += 1

        # 世界观补充
        wa = plan.get("worldview_additions") or {}
        for ck in wa.get("common_knowledge", []) or []:
            if ck:
                await self.add_common_knowledge(world_id, ck)
                applied["common_knowledge"] += 1
        append_bg = (wa.get("background_append") or "").strip()
        if append_bg and wv is not None:
            wv.background = ((wv.background or "") + "\n\n" + append_bg).strip()
            await self.db.commit()
            await self.log_event(world_id, "worldview_change", "世界导演补充了完整背景设定",
                                 {"append": append_bg[:200]}, in_world_time=t_next)
            applied["background_appended"] = True

        # 场景切换
        sc = plan.get("scene") or {}
        if sc.get("should_switch"):
            nxt = sc.get("next", {}) or {}
            prev = (await self.db.execute(select(Scene).where(Scene.world_id == world_id)
                    .order_by(Scene.id.desc()).limit(1))).scalar_one_or_none()
            new_scene = Scene(user_id=world.user_id, world_id=world_id, worldview_id=world.worldview_id,
                              name=nxt.get("name", "新场景"), scenario=nxt.get("setting", ""),
                              prev_scene_id=(prev.id if prev else None))
            new_scene = await self._save(new_scene)
            for order, nm in enumerate(nxt.get("participants", []) or []):
                ch = name_to_char.get(nm)
                self.db.add(SceneParticipant(scene_id=new_scene.id,
                            role_id=(ch.role_id if ch else None),
                            character_id=(ch.id if ch else None), role_name=nm, display_order=order))
            await self.db.commit()
            await self.log_event(world_id, "scene_change",
                                 f"开启新场景：{new_scene.name}", {"reason": sc.get("reason", "")},
                                 in_world_time=t_next)
            applied["scene_switched"] = True

        # 推进世界时间
        if t_next and t_next != world.in_world_time:
            before = world.in_world_time
            world.in_world_time = t_next
            await self.db.commit()
            await self.log_event(world_id, "time_advance", f"世界时间推进到「{t_next}」",
                                 {"before": before, "after": t_next}, in_world_time=t_next)

        return {"success": True, "day_summary": day_summary, "next_time": t_next, "applied": applied}
