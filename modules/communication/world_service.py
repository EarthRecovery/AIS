"""持久世界的读写编排：对 World 及其所有从属实体做 CRUD，

并在「语义性状态变更」(关系/物品易主/心智/认知/世界观/时间) 时追加一条
WorldEvent(含 before/after)，落实「可变当前态 + 追加事件日志」架构。
"""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy import delete, select
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
    async def create_character(self, world_id, name, role_id=None, status=None) -> Character:
        c = Character(world_id=world_id, name=name, role_id=role_id, status=status or "active")
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
    async def build_perception(self, world_id, character_id, scene_id=None):
        """构造某角色的感知切片：世界常识(公共) + 自己的私有记忆/认知 + 当前场景知识。"""
        commons = await self.list_common_knowledge(world_id)
        memories = await self.list_memories(character_id)
        scene_k = await self.list_scene_knowledge(scene_id) if scene_id else []
        return {
            "common_knowledge": [c.content for c in commons],
            "memories": [{"kind": m.kind, "content": m.content,
                          "confidence": m.confidence, "is_true": m.is_true} for m in memories],
            "scene_knowledge": [s.content for s in scene_k],
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
