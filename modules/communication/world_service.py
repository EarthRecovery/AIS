"""持久世界的读写编排：对 World 及其所有从属实体做 CRUD，

并在「语义性状态变更」(关系/物品易主/心智/认知/世界观/时间) 时追加一条
WorldEvent(含 before/after)，落实「可变当前态 + 追加事件日志」架构。
"""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from storage.db import get_db
from storage.models.ability import Ability
from storage.models.belief import Belief
from storage.models.character import Character
from storage.models.item import Item
from storage.models.location import Location
from storage.models.mental_state import MentalState
from storage.models.relationship import Relationship
from storage.models.world import World
from storage.models.world_event import WorldEvent
from storage.models.worldview import Worldview


def _apply(obj, data: dict):
    """把请求里非 None 的字段写到 ORM 对象上。"""
    for k, v in data.items():
        if v is not None:
            setattr(obj, k, v)


class WorldService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
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
        for model in (WorldEvent, Belief, Ability, MentalState, Relationship, Item, Location, Character):
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
        await self.db.execute(delete(Belief).where(Belief.holder_character_id == char_id))
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

    # ---- Belief（主观认知）----
    async def create_belief(self, world_id, data: dict):
        return await self._save(Belief(world_id=world_id, **{k: v for k, v in data.items() if v is not None}))

    async def update_belief(self, belief_id, data: dict):
        b = await self._get(Belief, belief_id)
        if not b:
            return None
        _apply(b, data)
        await self.db.commit()
        await self.db.refresh(b)
        await self.log_event(b.world_id, "belief_update", "认知更新",
                             {"belief_id": belief_id, "after": data},
                             actor=b.holder_character_id, in_world_time=await self._world_time(b.world_id))
        return b

    async def delete_belief(self, belief_id):
        await self.db.execute(delete(Belief).where(Belief.id == belief_id))
        await self.db.commit()
        return True

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
            beliefs = (await self.db.execute(
                select(Belief).where(Belief.holder_character_id == c.id))).scalars().all()
            char_blocks.append({"character": c, "mental": mental, "abilities": abilities, "beliefs": beliefs})
        locations = await self._all(Location, world_id=world_id)
        items = await self._all(Item, world_id=world_id)
        relationships = await self._all(Relationship, world_id=world_id)
        return {
            "world": world, "worldview": worldview, "characters": char_blocks,
            "locations": locations, "items": items, "relationships": relationships,
        }
