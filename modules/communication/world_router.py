"""持久世界管理 API：World 及其所有从属实体的增删改查。"""

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.security.deps import get_request_user_id
from modules.communication.simulation import SimulationService
from modules.communication.world_service import WorldService

router = APIRouter(prefix="/world", tags=["world"])


# ---------------- 序列化 ----------------
def s_world(w):
    return {"id": w.id, "name": w.name, "worldview_id": w.worldview_id,
            "in_world_time": w.in_world_time, "status": w.status}

def s_worldview(wv):
    return None if wv is None else {
        "id": wv.id, "name": wv.name, "description": wv.description, "rules": wv.rules,
        "background": wv.background}

def s_char(c):
    return {"id": c.id, "name": c.name, "role_id": c.role_id, "status": c.status,
            "current_location_id": c.current_location_id}

def s_mental(m):
    return None if m is None else {
        "id": m.id, "character_id": m.character_id, "mood": m.mood, "goals": m.goals,
        "motivation": m.motivation, "self_summary": m.self_summary}

def s_ability(a):
    return {"id": a.id, "character_id": a.character_id, "name": a.name,
            "description": a.description, "level": a.level}

def s_belief(b):
    # b 是 AgentMemory(kind='belief')；对外仍以 holder_character_id 暴露
    return {"id": b.id, "holder_character_id": b.character_id, "subject_type": b.subject_type,
            "subject_id": b.subject_id, "content": b.content, "confidence": b.confidence, "is_true": b.is_true}

def s_memory(m):
    return {"id": m.id, "character_id": m.character_id, "kind": m.kind, "content": m.content,
            "confidence": m.confidence, "is_true": m.is_true, "importance": m.importance,
            "source_scene_id": m.source_scene_id}

def s_common(c):
    return {"id": c.id, "content": c.content}

def s_sk(s):
    return {"id": s.id, "scene_id": s.scene_id, "content": s.content, "scope": s.scope}

def s_location(l):
    return {"id": l.id, "name": l.name, "type": l.type, "description": l.description,
            "parent_location_id": l.parent_location_id}

def s_item(i):
    return {"id": i.id, "name": i.name, "description": i.description,
            "owner_character_id": i.owner_character_id, "location_id": i.location_id, "state": i.state}

def s_rel(r):
    return {"id": r.id, "from_character_id": r.from_character_id, "to_character_id": r.to_character_id,
            "relation_type": r.relation_type, "affinity": r.affinity, "notes": r.notes}

def s_event(e):
    return {"id": e.id, "kind": e.kind, "summary": e.summary, "payload": e.payload,
            "actor_character_id": e.actor_character_id, "in_world_time": e.in_world_time}


# ---------------- 请求体 ----------------
class WorldCreate(BaseModel):
    name: str
    worldview_id: int | None = None

class WorldUpdate(BaseModel):
    name: str | None = None
    in_world_time: str | None = None
    status: str | None = None
    worldview_id: int | None = None

class WorldviewUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    rules: str | None = None
    background: str | None = None
    world_id: int | None = None

class CharacterCreate(BaseModel):
    name: str
    role_id: int | None = None
    status: str | None = None

class CharacterUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    current_location_id: int | None = None

class MentalUpdate(BaseModel):
    mood: str | None = None
    goals: str | None = None
    motivation: str | None = None
    self_summary: str | None = None

class AbilityCreate(BaseModel):
    name: str
    description: str | None = None
    level: int | None = None

class AbilityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    level: int | None = None

class BeliefCreate(BaseModel):
    holder_character_id: int
    subject_type: str
    subject_id: int | None = None
    content: str
    confidence: int | None = None
    is_true: bool | None = None

class BeliefUpdate(BaseModel):
    content: str | None = None
    confidence: int | None = None
    is_true: bool | None = None

class LocationCreate(BaseModel):
    name: str
    type: str | None = None
    description: str | None = None
    parent_location_id: int | None = None

class LocationUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    parent_location_id: int | None = None

class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    owner_character_id: int | None = None
    location_id: int | None = None
    state: dict | None = None

class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    owner_character_id: int | None = None
    location_id: int | None = None
    state: dict | None = None

class RelationshipCreate(BaseModel):
    from_character_id: int
    to_character_id: int
    relation_type: str | None = None
    affinity: int | None = None
    notes: str | None = None

class RelationshipUpdate(BaseModel):
    relation_type: str | None = None
    affinity: int | None = None
    notes: str | None = None


# ================= World =================
@router.post("/new")
async def create_world(req: WorldCreate, svc: WorldService = Depends(), user_id: str = Depends(get_request_user_id)):
    w = await svc.create_world(user_id, req.name, req.worldview_id)
    return s_world(w)

@router.get("/list")
async def list_worlds(svc: WorldService = Depends(), user_id: str = Depends(get_request_user_id)):
    return {"worlds": [s_world(w) for w in await svc.list_worlds(user_id)]}

@router.get("/worldview/list")
async def list_worldviews(svc: WorldService = Depends(), user_id: str = Depends(get_request_user_id)):
    return {"worldviews": [s_worldview(w) for w in await svc.list_worldviews(user_id)]}

@router.get("/{world_id}")
async def get_world(world_id: int, svc: WorldService = Depends()):
    d = await svc.world_detail(world_id)
    if d is None:
        return {"error": "world not found"}
    return {
        "world": s_world(d["world"]),
        "worldview": s_worldview(d["worldview"]),
        "characters": [
            {"character": s_char(b["character"]), "mental": s_mental(b["mental"]),
             "abilities": [s_ability(a) for a in b["abilities"]],
             "beliefs": [s_belief(x) for x in b["beliefs"]],
             "memories": [s_memory(m) for m in b.get("memories", [])]}
            for b in d["characters"]
        ],
        "locations": [s_location(l) for l in d["locations"]],
        "items": [s_item(i) for i in d["items"]],
        "relationships": [s_rel(r) for r in d["relationships"]],
    }

@router.patch("/{world_id}")
async def update_world(world_id: int, req: WorldUpdate, svc: WorldService = Depends()):
    w = await svc.update_world(world_id, req.model_dump(exclude_unset=True))
    return s_world(w) if w else {"error": "not found"}

@router.delete("/{world_id}")
async def delete_world(world_id: int, svc: WorldService = Depends()):
    await svc.delete_world(world_id)
    return {"success": True}

@router.get("/{world_id}/events")
async def get_events(world_id: int, svc: WorldService = Depends()):
    return {"events": [s_event(e) for e in await svc.get_events(world_id)]}


# ================= Worldview =================
@router.patch("/worldview/{worldview_id}")
async def update_worldview(worldview_id: int, req: WorldviewUpdate, svc: WorldService = Depends()):
    data = req.model_dump(exclude_unset=True)
    world_id = data.pop("world_id", None)
    wv = await svc.update_worldview(worldview_id, data, world_id)
    return s_worldview(wv) if wv else {"error": "not found"}


# ================= Character =================
@router.post("/{world_id}/character")
async def create_character(world_id: int, req: CharacterCreate, svc: WorldService = Depends()):
    return s_char(await svc.create_character(world_id, req.name, req.role_id, req.status))

@router.patch("/character/{char_id}")
async def update_character(char_id: int, req: CharacterUpdate, svc: WorldService = Depends()):
    c = await svc.update_character(char_id, req.model_dump(exclude_unset=True))
    return s_char(c) if c else {"error": "not found"}

@router.delete("/character/{char_id}")
async def delete_character(char_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_character(char_id)}

@router.put("/character/{char_id}/mental")
async def upsert_mental(char_id: int, req: MentalUpdate, svc: WorldService = Depends()):
    return s_mental(await svc.upsert_mental(char_id, req.model_dump(exclude_unset=True)))

@router.post("/character/{char_id}/ability")
async def create_ability(char_id: int, req: AbilityCreate, svc: WorldService = Depends()):
    return s_ability(await svc.create_ability(char_id, req.name, req.description, req.level))

@router.patch("/ability/{ability_id}")
async def update_ability(ability_id: int, req: AbilityUpdate, svc: WorldService = Depends()):
    a = await svc.update_ability(ability_id, req.model_dump(exclude_unset=True))
    return s_ability(a) if a else {"error": "not found"}

@router.delete("/ability/{ability_id}")
async def delete_ability(ability_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_ability(ability_id)}

@router.post("/{world_id}/belief")
async def create_belief(world_id: int, req: BeliefCreate, svc: WorldService = Depends()):
    return s_belief(await svc.create_belief(world_id, req.model_dump(exclude_unset=True)))

@router.patch("/belief/{belief_id}")
async def update_belief(belief_id: int, req: BeliefUpdate, svc: WorldService = Depends()):
    b = await svc.update_belief(belief_id, req.model_dump(exclude_unset=True))
    return s_belief(b) if b else {"error": "not found"}

@router.delete("/belief/{belief_id}")
async def delete_belief(belief_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_belief(belief_id)}


# ================= Location =================
@router.post("/{world_id}/location")
async def create_location(world_id: int, req: LocationCreate, svc: WorldService = Depends()):
    return s_location(await svc.create_location(world_id, req.model_dump(exclude_unset=True)))

@router.patch("/location/{loc_id}")
async def update_location(loc_id: int, req: LocationUpdate, svc: WorldService = Depends()):
    l = await svc.update_location(loc_id, req.model_dump(exclude_unset=True))
    return s_location(l) if l else {"error": "not found"}

@router.delete("/location/{loc_id}")
async def delete_location(loc_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_location(loc_id)}


# ================= Item =================
@router.post("/{world_id}/item")
async def create_item(world_id: int, req: ItemCreate, svc: WorldService = Depends()):
    return s_item(await svc.create_item(world_id, req.model_dump(exclude_unset=True)))

@router.patch("/item/{item_id}")
async def update_item(item_id: int, req: ItemUpdate, svc: WorldService = Depends()):
    i = await svc.update_item(item_id, req.model_dump(exclude_unset=True))
    return s_item(i) if i else {"error": "not found"}

@router.delete("/item/{item_id}")
async def delete_item(item_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_item(item_id)}


# ================= Relationship =================
@router.post("/{world_id}/relationship")
async def create_relationship(world_id: int, req: RelationshipCreate, svc: WorldService = Depends()):
    return s_rel(await svc.create_relationship(world_id, req.model_dump(exclude_unset=True)))

@router.patch("/relationship/{rel_id}")
async def update_relationship(rel_id: int, req: RelationshipUpdate, svc: WorldService = Depends()):
    r = await svc.update_relationship(rel_id, req.model_dump(exclude_unset=True))
    return s_rel(r) if r else {"error": "not found"}

@router.delete("/relationship/{rel_id}")
async def delete_relationship(rel_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_relationship(rel_id)}


# ================= CommonKnowledge（世界常识，所有 agent 可见）=================
class ContentReq(BaseModel):
    content: str

@router.post("/{world_id}/common")
async def add_common(world_id: int, req: ContentReq, svc: WorldService = Depends()):
    return s_common(await svc.add_common_knowledge(world_id, req.content))

@router.get("/{world_id}/common")
async def list_common(world_id: int, svc: WorldService = Depends()):
    return {"common_knowledge": [s_common(c) for c in await svc.list_common_knowledge(world_id)]}

@router.delete("/common/{ck_id}")
async def delete_common(ck_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_common_knowledge(ck_id)}


# ================= AgentMemory（角色私有记忆）=================
class MemoryCreate(BaseModel):
    character_id: int
    content: str
    kind: str | None = "memory"
    importance: int | None = 0

@router.post("/{world_id}/memory")
async def add_memory(world_id: int, req: MemoryCreate, svc: WorldService = Depends()):
    m = await svc.add_memory(world_id, req.character_id, req.content,
                             kind=req.kind or "memory", importance=req.importance or 0)
    return s_memory(m)

@router.get("/character/{char_id}/memory")
async def list_memory(char_id: int, svc: WorldService = Depends()):
    return {"memories": [s_memory(m) for m in await svc.list_memories(char_id)]}

@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_memory(memory_id)}


# ================= SceneKnowledge（场景知识，在场 agent 可获知）=================
class SceneKnowReq(BaseModel):
    content: str
    scope: str | None = "public"

@router.post("/scene/{scene_id}/knowledge")
async def add_scene_knowledge(scene_id: int, req: SceneKnowReq, svc: WorldService = Depends()):
    return s_sk(await svc.add_scene_knowledge(scene_id, req.content, req.scope or "public"))

@router.get("/scene/{scene_id}/knowledge")
async def list_scene_knowledge(scene_id: int, svc: WorldService = Depends()):
    return {"scene_knowledge": [s_sk(s) for s in await svc.list_scene_knowledge(scene_id)]}

@router.delete("/scene-knowledge/{sk_id}")
async def delete_scene_knowledge(sk_id: int, svc: WorldService = Depends()):
    return {"success": await svc.delete_scene_knowledge(sk_id)}


# ================= 感知视图 & Keeper =================
@router.get("/{world_id}/character/{char_id}/perception")
async def get_perception(world_id: int, char_id: int, scene_id: int | None = None,
                         svc: WorldService = Depends()):
    return await svc.build_perception(world_id, char_id, scene_id)

@router.post("/scene/{scene_id}/keeper")
async def keeper_digest(scene_id: int, svc: WorldService = Depends()):
    """记录官消化一个场景：写各在场角色的私有记忆，并决定是否切换场景。"""
    return await svc.keeper_digest_scene(scene_id)


# ================= 每日结算 / 世界推演 =================
class AdvanceDayRequest(BaseModel):
    directive: str | None = None

@router.post("/{world_id}/advance-day")
async def advance_day(world_id: int, req: AdvanceDayRequest, svc: WorldService = Depends()):
    """把世界推进一天：拍快照后由世界导演自动推演并应用全部变化。"""
    return await svc.advance_day(world_id, (req.directive or ""))

@router.post("/{world_id}/rollback-day")
async def rollback_day(world_id: int, svc: WorldService = Depends()):
    """回退一天：恢复最近一张结算前快照。"""
    return await svc.rollback_day(world_id)

@router.get("/{world_id}/can-rollback")
async def can_rollback(world_id: int, svc: WorldService = Depends()):
    return {"can_rollback": await svc.has_snapshot(world_id)}


# ================= 真实推演（演播室）=================
class SimDirective(BaseModel):
    directive: str | None = None

@router.get("/{world_id}/sim/status")
async def sim_status(world_id: int, svc: SimulationService = Depends()):
    return await svc.status(world_id)

@router.post("/{world_id}/sim/scene")
async def sim_open_scene(world_id: int, req: SimDirective, svc: SimulationService = Depends()):
    return await svc.open_scene(world_id, req.directive or "")

@router.post("/{world_id}/sim/step")
async def sim_step(world_id: int, req: SimDirective, svc: SimulationService = Depends()):
    return await svc.step_round(world_id, req.directive or "")

@router.post("/{world_id}/sim/step/stream")
async def sim_step_stream(world_id: int, req: SimDirective, svc: SimulationService = Depends()):
    async def gen():
        async for ev in svc.step_round_stream(world_id, req.directive or ""):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\r\n\r\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@router.post("/{world_id}/sim/new-chapter")
async def sim_new_chapter(world_id: int, req: SimDirective, svc: SimulationService = Depends()):
    """新建章节：拍快照 → 进入下一章 → 开本章第一幕。"""
    return await svc.new_chapter(world_id, req.directive or "")

@router.post("/{world_id}/sim/run-chapter")
async def sim_run_chapter(world_id: int, req: SimDirective, svc: SimulationService = Depends()):
    return await svc.run_chapter(world_id, req.directive or "")

@router.post("/{world_id}/sim/rollback-chapter")
async def sim_rollback_chapter(world_id: int, svc: SimulationService = Depends()):
    """回退章节：恢复最近一张快照（本章开篇前的状态）。"""
    return await svc.rollback_chapter(world_id)

@router.get("/{world_id}/character/{char_id}/detail")
async def character_detail(world_id: int, char_id: int, svc: WorldService = Depends()):
    d = await svc.character_detail(world_id, char_id)
    return d or {"error": "not found"}

@router.get("/scene/{scene_id}/messages")
async def sim_scene_messages(scene_id: int, svc: SimulationService = Depends()):
    return await svc.scene_messages(scene_id)


# ================= 剧本大纲 =================
@router.post("/{world_id}/outline/generate")
async def outline_generate(world_id: int, req: SimDirective, svc: WorldService = Depends()):
    beats = await svc.generate_outline(world_id, req.directive or "")
    return {"outline": beats}
