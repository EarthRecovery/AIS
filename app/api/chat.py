from app.services.turn_service import TurnService
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from app.services.chat_service import ChatService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, svc: ChatService = Depends()):
    reply = await svc.chat(req.message)
    return ChatResponse(reply=reply)

@router.post("/chat/stream")
async def chat_stream_post(req: ChatRequest, svc: ChatService = Depends()):
    async def event_generator():
        async for chunk in svc.chat_stream(req.message):
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
async def start_new_chat(svc: ChatService = Depends()):
    result = await svc.start_new_chat()
    return {"success": result}

@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: int, svc: ChatService = Depends()):
    result = await svc.delete_chat(chat_id)
    if result:
        return {"success": True}
    else:
        return {"success": False, "error": "Chat ID not found"}
    
@router.get("/chat/history_debug")
async def show_all_turn_data(svc: ChatService = Depends()):
    histories = await svc.show_all_turn_data()
    return histories

@router.get("/chat/turnid")
async def get_current_turn_id(svc: ChatService = Depends()):
    turn_id = await svc.get_current_turn_id()
    return {"turn_id": turn_id}

@router.get("/chat/history/{turn_id}")
async def get_chat_history(turn_id: int, svc: ChatService = Depends()):
    histories = await svc.show_all_turn_data()
    if turn_id in histories:
        return histories[turn_id]
    else:
        return {"error": "Turn ID not found"}
