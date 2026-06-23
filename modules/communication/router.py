import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.security.deps import get_request_user_id
from modules.communication.service import CommunicationService

router = APIRouter(prefix="/communication", tags=["communication"])


# ---------------- 请求体 ----------------
class WorldviewRequest(BaseModel):
    name: str
    description: str | None = None
    rules: str | None = None
    background: str | None = None


class RoomRequest(BaseModel):
    name: str
    worldview_id: int
    scenario: str | None = None
    role_ids: list[int]


class SayRequest(BaseModel):
    content: str
    target_role_id: int | None = None


class AdvanceRequest(BaseModel):
    target_role_id: int | None = None


def _sse(gen):
    """把事件 dict 异步生成器包成 SSE（每个事件一行 JSON）。"""
    async def event_generator():
        async for ev in gen:
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\r\n\r\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------- 世界观 ----------------
@router.post("/worldview")
async def create_worldview(
    req: WorldviewRequest,
    svc: CommunicationService = Depends(),
    user_id: str = Depends(get_request_user_id),
):
    wv = await svc.create_worldview(user_id, req.name, req.description or "", req.rules or "",
                                    req.background or "")
    return {"id": wv.id, "name": wv.name}


@router.get("/worldview/list")
async def list_worldviews(
    svc: CommunicationService = Depends(), user_id: str = Depends(get_request_user_id)
):
    items = await svc.list_worldviews(user_id)
    return {
        "worldviews": [
            {"id": w.id, "name": w.name, "description": w.description, "rules": w.rules,
             "background": w.background}
            for w in items
        ]
    }


# ---------------- 房间 ----------------
@router.post("/room/new")
async def create_room(
    req: RoomRequest,
    svc: CommunicationService = Depends(),
    user_id: str = Depends(get_request_user_id),
):
    room = await svc.create_room(
        user_id, req.name, req.worldview_id, req.scenario or "", req.role_ids
    )
    return {"id": room.id, "name": room.name, "worldview_id": room.worldview_id}


@router.get("/room/list")
async def list_rooms(
    svc: CommunicationService = Depends(), user_id: str = Depends(get_request_user_id)
):
    rooms = await svc.list_rooms(user_id)
    return {
        "rooms": [
            {"id": r.id, "name": r.name, "worldview_id": r.worldview_id, "summary": r.summary}
            for r in rooms
        ]
    }


@router.get("/room/{room_id}")
async def get_room_detail(room_id: int, svc: CommunicationService = Depends()):
    room = await svc.get_room(room_id)
    if room is None:
        return {"error": "room not found"}
    worldview = await svc.get_worldview(room.worldview_id)
    participants = await svc.get_participants(room_id)
    messages = await svc.get_messages(room_id)
    return {
        "room": {"id": room.id, "name": room.name, "scenario": room.scenario},
        "worldview": None
        if worldview is None
        else {
            "id": worldview.id,
            "name": worldview.name,
            "description": worldview.description,
            "rules": worldview.rules,
        },
        "participants": [
            {"role_id": p.role_id, "name": p.role_name} for p in participants
        ],
        "messages": [
            {
                "id": m.id,
                "speaker_type": m.speaker_type,
                "speaker_role_id": m.speaker_role_id,
                "speaker_name": m.speaker_name,
                "content": m.content,
            }
            for m in messages
        ],
    }


@router.delete("/room/{room_id}")
async def delete_room(room_id: int, svc: CommunicationService = Depends()):
    await svc.delete_room(room_id)
    return {"success": True}


# ---------------- 发言 / 推进（SSE）----------------
@router.post("/room/{room_id}/say/stream")
async def say_stream(
    room_id: int,
    req: SayRequest,
    svc: CommunicationService = Depends(),
    user_id: str = Depends(get_request_user_id),
):
    return _sse(svc.say_stream(room_id, user_id, req.content, req.target_role_id))


@router.post("/room/{room_id}/advance/stream")
async def advance_stream(
    room_id: int,
    req: AdvanceRequest,
    svc: CommunicationService = Depends(),
    user_id: str = Depends(get_request_user_id),
):
    return _sse(svc.advance_stream(room_id, user_id, req.target_role_id))
