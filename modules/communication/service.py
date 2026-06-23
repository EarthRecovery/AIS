"""communication：场景化多人格 + 共享世界观的交流编排。

以现有单人格系统为基础：
- 人格直接复用 ais_roles（Role / RoleSetting）。
- 世界观(Worldview) 是一段被场景内所有人格共享、注入到各自 prompt 的设定。
- 场景(Scene) = 一个世界观 + 一组参与人格 + 一条多人发言记录(SceneMessage)。
- "下一个谁说话"：用户可手动指定(target_role_id)，否则由导演 LLM 选。

注：路由层仍沿用 /communication/room/* 路径与 room_* 方法名（对外不变），
底层数据模型已是 Scene。世界级的记忆/感知/场景切换由 world_service + Keeper 处理。
"""

from typing import List, Optional

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.clients.llm_client import LLMClient
from modules.deps import get_llm_client
from modules.role.service import RoleService
from storage.db import get_db
from storage.models.scene import Scene
from storage.models.scene_message import SceneMessage
from storage.models.scene_participant import SceneParticipant
from storage.models.worldview import Worldview


class CommunicationService:
    def __init__(
        self,
        llm: LLMClient = Depends(get_llm_client),
        db: AsyncSession = Depends(get_db),
    ):
        self.llm = llm
        self.db = db

    # ---------------- 世界观 ----------------
    async def create_worldview(self, user_id: int, name: str, description: str, rules: str,
                               background: str = "") -> Worldview:
        wv = Worldview(user_id=user_id, name=name, description=description, rules=rules,
                       background=background)
        self.db.add(wv)
        await self.db.commit()
        await self.db.refresh(wv)
        return wv

    async def list_worldviews(self, user_id: int) -> List[Worldview]:
        res = await self.db.execute(
            select(Worldview).where(Worldview.user_id == user_id).order_by(Worldview.id.desc())
        )
        return res.scalars().all()

    async def get_worldview(self, worldview_id: int) -> Optional[Worldview]:
        res = await self.db.execute(select(Worldview).where(Worldview.id == worldview_id))
        return res.scalar_one_or_none()

    @staticmethod
    def _worldview_text(wv: Optional[Worldview]) -> str:
        if not wv:
            return ""
        parts = []
        if wv.description:
            parts.append(wv.description.strip())
        if wv.rules:
            parts.append("【世界规则】\n" + wv.rules.strip())
        return "\n\n".join(parts)

    # ---------------- 场景（对外仍叫 room） ----------------
    async def create_room(
        self, user_id: int, name: str, worldview_id: int, scenario: str, role_ids: List[int],
        world_id: Optional[int] = None,
    ) -> Scene:
        scene = Scene(user_id=user_id, name=name, worldview_id=worldview_id,
                      scenario=scenario, world_id=world_id)
        self.db.add(scene)
        await self.db.commit()
        await self.db.refresh(scene)

        role_service = RoleService(db=self.db)
        for order, rid in enumerate(role_ids):
            role_name = await role_service.get_role_name_by_id(rid) or f"角色{rid}"
            self.db.add(
                SceneParticipant(
                    scene_id=scene.id, role_id=rid, role_name=role_name, display_order=order
                )
            )
        await self.db.commit()
        return scene

    async def list_rooms(self, user_id: int) -> List[Scene]:
        res = await self.db.execute(
            select(Scene).where(Scene.user_id == user_id).order_by(Scene.id.desc())
        )
        return res.scalars().all()

    async def get_room(self, room_id: int) -> Optional[Scene]:
        res = await self.db.execute(select(Scene).where(Scene.id == room_id))
        return res.scalar_one_or_none()

    async def get_participants(self, room_id: int) -> List[SceneParticipant]:
        res = await self.db.execute(
            select(SceneParticipant)
            .where(SceneParticipant.scene_id == room_id)
            .order_by(SceneParticipant.display_order, SceneParticipant.id)
        )
        return res.scalars().all()

    async def get_messages(self, room_id: int) -> List[SceneMessage]:
        res = await self.db.execute(
            select(SceneMessage)
            .where(SceneMessage.scene_id == room_id)
            .order_by(SceneMessage.timestamp, SceneMessage.id)
        )
        return res.scalars().all()

    async def delete_room(self, room_id: int) -> bool:
        await self.db.execute(delete(SceneMessage).where(SceneMessage.scene_id == room_id))
        await self.db.execute(delete(SceneParticipant).where(SceneParticipant.scene_id == room_id))
        await self.db.execute(delete(Scene).where(Scene.id == room_id))
        await self.db.commit()
        return True

    async def add_message(
        self, room_id: int, speaker_type: str, speaker_name: str, content: str,
        speaker_role_id: Optional[int] = None,
    ) -> SceneMessage:
        msg = SceneMessage(
            scene_id=room_id,
            speaker_type=speaker_type,
            speaker_role_id=speaker_role_id,
            speaker_name=speaker_name,
            content=content,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    # ---------------- 编排辅助 ----------------
    async def _build_roster(self, participants: List[SceneParticipant]) -> List[dict]:
        """在场角色名单：name + 简短设定，给导演选人 & 给人格了解同场角色。"""
        role_service = RoleService(db=self.db)
        roster = []
        for p in participants:
            setting = await role_service.get_role_setting_by_id(p.role_id)
            desc = setting.get_description() if setting else ""
            roster.append({"role_id": p.role_id, "name": p.role_name, "description": desc})
        return roster

    @staticmethod
    def _build_transcript(messages: List[SceneMessage]) -> List[dict]:
        return [{"speaker_name": m.speaker_name, "content": m.content} for m in messages]

    async def _resolve_speaker(
        self, participants, roster, transcript, target_role_id: Optional[int]
    ) -> Optional[dict]:
        """决定下一个发言者：手动指定优先，否则导演选。返回 roster 中的一项。"""
        if not roster:
            return None
        if target_role_id:
            for r in roster:
                if r["role_id"] == target_role_id:
                    return r
        last_speaker = transcript[-1]["speaker_name"] if transcript else None
        name = await self.llm.choose_next_speaker(roster, transcript, last_speaker)
        for r in roster:
            if r["name"] == name:
                return r
        return roster[0]

    async def _stream_persona_turn(self, scene: Scene, speaker: dict, transcript: List[dict]):
        """让选定人格在场景里流式发言，并落库。yields 事件 dict。"""
        wv = await self.get_worldview(scene.worldview_id)
        worldview_text = self._worldview_text(wv)
        participants = await self.get_participants(scene.id)
        roster = await self._build_roster(participants)

        role_service = RoleService(db=self.db)
        setting = await role_service.get_role_setting_by_id(speaker["role_id"])
        persona_settings = setting.to_json() if setting else {"name": speaker["name"]}

        # 若场景属于某个持久世界：给发言角色构造「感知视图」（世界常识 + 自己的私有记忆 + 场景知识），
        # 让它只依据自己知道的信息发言（默认私有，互不可见）。
        perception = None
        if scene.world_id:
            from modules.communication.world_service import WorldService
            ws = WorldService(llm=self.llm, db=self.db)
            ch = await ws.character_by_name(scene.world_id, speaker["name"])
            if ch is not None:
                perception = await ws.build_perception(scene.world_id, ch.id, scene.id)

        yield {"type": "speaker", "role_id": speaker["role_id"], "name": speaker["name"]}

        collected = ""
        async for chunk in self.llm.group_chat_stream_perceived(
            persona_settings, worldview_text, scene.scenario, roster, transcript, perception
        ):
            collected += chunk
            yield {"type": "token", "text": chunk}

        await self.add_message(
            room_id=scene.id,
            speaker_type="persona",
            speaker_name=speaker["name"],
            content=collected,
            speaker_role_id=speaker["role_id"],
        )
        yield {"type": "done", "role_id": speaker["role_id"], "name": speaker["name"]}

    # ---------------- 对外：发言 / 推进 ----------------
    async def say_stream(self, room_id: int, user_id: int, content: str, target_role_id: Optional[int]):
        scene = await self.get_room(room_id)
        if scene is None:
            yield {"type": "error", "message": "场景不存在"}
            return
        # 用户发言落库
        if content and content.strip():
            await self.add_message(room_id, "user", "你", content.strip())

        participants = await self.get_participants(room_id)
        messages = await self.get_messages(room_id)
        transcript = self._build_transcript(messages)
        roster = await self._build_roster(participants)

        speaker = await self._resolve_speaker(participants, roster, transcript, target_role_id)
        if speaker is None:
            yield {"type": "error", "message": "场景内没有可发言的角色"}
            return
        async for ev in self._stream_persona_turn(scene, speaker, transcript):
            yield ev

    async def advance_stream(self, room_id: int, user_id: int, target_role_id: Optional[int] = None):
        """无用户输入，让人格之间自动接话（导演选下一个，或手动指定）。"""
        async for ev in self.say_stream(room_id, user_id, "", target_role_id):
            yield ev
