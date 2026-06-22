from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class SceneParticipant(Base):
    """场景在场者：把人格(role)或持久角色(character)关联进某个场景。

    独立聊天用 role_id；持久世界里的场景用 character_id(角色带记忆延续)。
    在场是 agent 能否获知场景知识的前提。
    """

    __tablename__ = "ais_scene_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, nullable=True)
    character_id: Mapped[int] = mapped_column(Integer, nullable=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
