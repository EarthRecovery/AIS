from fastapi import APIRouter, Depends
from pydantic import BaseModel
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

@router.post("/chat/new")
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
