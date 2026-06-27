from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class SceneMessage(Base):
    """场景内的一条发言。speaker_type 区分用户 / 人格 / 旁白。"""

    __tablename__ = "ais_scene_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # "user" | "persona" | "narrator"
    speaker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    speaker_role_id: Mapped[int] = mapped_column(Integer, nullable=True)
    speaker_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # say(台词,默认) / do(动作,他人可感知) / think(心理,私有,仅本人+Keeper)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="say", server_default="say")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
