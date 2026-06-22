from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Worldview(Base):
    """共享世界观：一个房间内所有人格共用的世界设定 / 背景 / 规则。"""

    __tablename__ = "ais_worldviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 世界背景设定（地点、时代、阵营、基调等）
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # 世界规则 / 约束（魔法体系、禁忌、物理法则等）
    rules: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
