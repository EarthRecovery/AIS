from app.infra.llm_client import LLMClient
from app.services.deps import get_llm_client, get_rag_client
from fastapi import Depends
from app.db import get_db
from app.models.role import Role
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.role_setting import RoleSetting

class RoleService:

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def set_role(self, name: str, role_setting: RoleSetting):
        result = await self.db.execute(select(Role).where(Role.name == name))
        role = result.scalars().first()
        if role:
            role.settings = role_setting.to_json()
        else:
            role = Role(
                name=name,
                settings=role_setting.to_json()
            )
            self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_role_setting_by_name(self, name: str):
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        role = result.scalars().first()
        if role:
            role_setting = RoleSetting()
            role_setting.from_json(role.settings)
            return role_setting
        return None
    
    async def get_role_setting_by_id(self, role_id: int):
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalars().first()
        if role:
            role_setting = RoleSetting()
            role_setting.from_json(role.settings)
            return role_setting
        return None
    
    async def get_role_name_by_id(self, role_id: int):
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalars().first()
        if role:
            return role.name
        return None

    async def list_roles(self):
        result = await self.db.execute(select(Role))
        roles = result.scalars().all()
        return roles