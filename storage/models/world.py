from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class World(Base):
    """持久世界容器：长期、不间断的多智能体仿真的顶层实体。

    拥有角色 / 地点 / 物品 / 时间线，并持有一个「当前世界观」(可被更改)。
    现有 Room 降级为这个世界里的一个「场景 / 会话」(Room.world_id)。
    """

    __tablename__ = "ais_worlds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 当前生效的世界观(指向 ais_worldviews)；更改世界观=换指向并记一条 WorldEvent
    worldview_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 世界内时间(可叙事化，如 "第3天 黄昏")，随推进而变化
    in_world_time: Mapped[str] = mapped_column(String(50), nullable=False, default="第1天 清晨")
    # active / paused / archived
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # 剧本大纲：[{title, goal}, ...]，指导长线推演不漂移、能收束到结局
    outline: Mapped[list] = mapped_column(JSON, nullable=True)
    # 当前推进到第几个节拍(对应 outline 下标)
    beat_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
