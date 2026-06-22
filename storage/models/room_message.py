from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class RoomMessage(Base):
    """房间内的一条发言。speaker_type 区分用户 / 人格 / 旁白。"""

    __tablename__ = "ais_comm_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # "user" | "persona" | "narrator"
    speaker_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # persona 发言时记录对应的 role_id；user / narrator 为空
    speaker_role_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 发言者展示名（人格名 / "你" / "旁白"）
    speaker_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
