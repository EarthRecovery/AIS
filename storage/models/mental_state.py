from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class MentalState(Base):
    """角色自身的「心智模型」当前态：情绪、目标、动机、自我记忆摘要。

    每个角色一条当前态；演化历史通过 WorldEvent(kind='mental_update') 追溯。
    """

    __tablename__ = "ais_mental_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 当前情绪 / 心境
    mood: Mapped[str] = mapped_column(String(100), nullable=True)
    # 当前目标(可多行)
    goals: Mapped[str] = mapped_column(Text, nullable=True)
    # 行为动机 / 价值取向
    motivation: Mapped[str] = mapped_column(Text, nullable=True)
    # 自我记忆 / 经历的滚动摘要(支撑长期连续性)
    self_summary: Mapped[str] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
