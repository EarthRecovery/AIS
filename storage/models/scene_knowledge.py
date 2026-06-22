from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class SceneKnowledge(Base):
    """场景知识：在该场景里、在场 agent 可以获知的信息。

    被某 agent 获知后，由 Keeper 写入该 agent 的私有记忆(AgentMemory)。
    scope 预留：public=在场都能知道，可扩展为限定某些角色。
    """

    __tablename__ = "ais_scene_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # public（在场皆可知）/ 其它可扩展
    scope: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
