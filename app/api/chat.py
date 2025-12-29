from app.security.deps import get_request_user_id
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, status, Request
from app.services.chat_service import ChatService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history_id: int

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, svc: ChatService = Depends(), user_id: str = Depends(get_request_user_id)):
    reply = await svc.chat(req.message, req.history_id, user_id=user_id)
    return ChatResponse(reply=reply)

@router.post("/chat/stream")
async def chat_stream_post(req: ChatRequest, svc: ChatService = Depends(), user_id: str = Depends(get_request_user_id)):
    async def event_generator():
        async for chunk in svc.chat_stream(req.message, req.history_id, user_id=user_id):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/chat/new")
async def start_new_chat(svc: ChatService = Depends(), user_id: str = Depends(get_request_user_id)):
    result = await svc.start_new_chat(user_id)
    return {"success": result}

@router.delete("/chat/{history_id}")
async def delete_chat(history_id: int, svc: ChatService = Depends()):
    result = await svc.delete_chat(history_id)
    if result:
        return {"success": True}
    else:
        return {"success": False, "error": "Chat ID not found"}

@router.get("/chat/history/{history_id}")
async def get_chat_history(history_id: int, svc: ChatService = Depends()):
    histories = await svc.get_chat_history_by_history_id(history_id)
    if histories:
        return histories
    else:
        return []
            
@router.get("/turns/history")
async def get_turn_list(svc: ChatService = Depends(), user_id: str = Depends(get_request_user_id)):
    turn_list = await svc.get_chat_histories_by_user_id(user_id)
    return {"turns": turn_list}

@router.post("/turns/change/{turn_id}")
async def change_to_turn(turn_id: int, svc: ChatService = Depends()):
    return {"success": True}
