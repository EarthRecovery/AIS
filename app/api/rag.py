from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.rag_service import RagService
from fastapi import BackgroundTasks

router = APIRouter()

class AddContextRequest(BaseModel):
    context: str
    channel: str = "default"

@router.get("/rag/is_service_available")
async def is_service_available(svc: RagService = Depends()):
    available = svc.is_service_available()
    return {"available": available}

@router.post("/rag/add_context")
def add_context(
    request: AddContextRequest,
    background_tasks: BackgroundTasks,
    svc: RagService = Depends()
):
    if not svc.is_service_available():
        return {"success": False, "error": "RAG service is not available"}

    background_tasks.add_task(
        svc.add_context,
        request.context,
        request.channel
    )

    return {
        "success": True,
        "status": "scheduled"
    }

@router.get("/rag/clear_collection/{collection_name}")
async def clear_collection(collection_name: str, svc: RagService = Depends()):
    result = await svc.clear_collection(collection_name)
    return {"success": result}

@router.get("/rag/get_vector_line_count/{collection_name}")
async def get_vector_line_count(collection_name: str, svc: RagService = Depends()):
    count = await svc.get_vector_line_count(collection_name)
    return {"line_count": count}

@router.get("/rag/get_collection_names")
async def get_collection_names(svc: RagService = Depends()):
    names = await svc.get_collection_names()
    return {"collection_names": names}