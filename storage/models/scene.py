from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Scene(Base):
    """场景：所有对话都发生在场景里（由 Room 演进而来）。

    可独立存在(一次性多人聊天, world_id 空)，也可作为某个持久 World 里的一幕。
    场景的开/合与切换由「记录官 Keeper」决定(status / prev_scene_id)。
    """

    __tablename__ = "ais_scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 所属持久世界(ais_worlds.id)；为空=独立的一次性场景
    world_id: Mapped[int] = mapped_column(Integer, nullable=True)
    worldview_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 场景设定 / 开场情境
    scenario: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=True)
    # active 进行中 / ended 已结束
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # 上一幕场景(由 Keeper 切换时记录因果链)
    prev_scene_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 该场景所属的世界内"天"(用于演播室按天分组/回放)
    day_label: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
