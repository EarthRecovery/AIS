from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, model_validator

from app.services.auth_service import AuthService
from app.services.role_service import RoleService
from app.models.role_setting import RoleSetting


router = APIRouter(prefix="/role", tags=["role"])

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
    
