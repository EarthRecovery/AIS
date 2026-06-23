from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, EmailStr, model_validator

from modules.auth.service import AuthService
from modules.rag.service import RagService
from modules.role.service import RoleService
from storage.models.role_setting import RoleSetting


router = APIRouter(prefix="/role", tags=["role"])


class KnowledgeRequest(BaseModel):
    text: str

class ExampleDialogue(BaseModel):
    role: str
    content: str

class SetRoleRequest(BaseModel):
    name: str
    rag_name: str | None = None
    description: str | None = None
    personality: list[str] | None = None
    scenario: str | None = None
    example_dialogues: list[ExampleDialogue] | None = None
    

@router.post("/set")
async def set_role(req: SetRoleRequest, svc: RoleService = Depends()):
    role_setting = RoleSetting()
    role_setting.set_name(req.name)
    if req.description:
        role_setting.set_description(req.description)
    if req.personality:
        for trait in req.personality:
            role_setting.add_personality_trait(trait)
    if req.example_dialogues:
        for dialogue in req.example_dialogues:
            role_setting.add_example_dialogue(dialogue.model_dump())
    if req.scenario:
        role_setting.set_scenario(req.scenario)
    if req.rag_name:
        role_setting.set_rag_name(req.rag_name)
    role = await svc.set_role(name=req.name, role_setting=role_setting)
    return {"status": "success", "role_id": role.id}

@router.get("/get/{name}")
async def get_role(name: str, svc: RoleService = Depends()):
    role_setting = await svc.get_role_setting_by_name(name)
    if role_setting:
        return {
            "name": role_setting.get_name(),
            "rag_name": role_setting.get_rag_name(),
            "description": role_setting.get_description(),
            "personality": role_setting.get_personality(),
            "example_dialogues": role_setting.get_example_dialogues(),
            "scenario": role_setting.get_scenario(),
        }
    return {"error": "Role not found"}

@router.get("/list")
async def list_roles(svc: RoleService = Depends()):
    roles = await svc.list_roles()
    role_list = []
    for role in roles:
        role_list.append({
            "id": role.id,
            "name": role.name,
            "settings": role.settings,
        })
    return {"roles": role_list}


@router.post("/{role_id}/knowledge")
async def add_role_knowledge(
    role_id: int,
    req: KnowledgeRequest,
    svc: RoleService = Depends(),
    rag: RagService = Depends(),
):
    """把一段文本作为该角色的知识库：后端分段索引到 collection=role_<id>，
    并把角色的 rag_name 指向该 collection，使对话时能检索到。"""
    text = (req.text or "").strip()
    if not text:
        return {"success": False, "error": "知识内容为空"}
    if not rag.is_service_available():
        return {"success": False, "error": "RAG 服务不可用"}
    collection = f"role_{role_id}"
    # 索引（含 OpenAI 嵌入，阻塞）放到线程池，避免卡住事件循环
    count = await run_in_threadpool(rag.index_text, text, collection)
    await svc.set_rag_name(role_id, collection)
    return {"success": True, "chunks": count, "rag_name": collection}
    
