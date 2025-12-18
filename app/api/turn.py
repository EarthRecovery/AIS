from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.turn_service import TurnService

router = APIRouter()

@router.get("/turns/history")
async def get_turn_list(svc: TurnService = Depends()):
    turn_list = await svc.get_turn_list()
    return {"turns": turn_list}

@router.post("/turns/change/{turn_id}")
async def change_to_turn(turn_id: int, svc: TurnService = Depends()):
    result = await svc.change_to_turn(turn_id)
    if result:
        return {"success": True}
    else:
        return {"success": False, "error": "Turn ID not found"}