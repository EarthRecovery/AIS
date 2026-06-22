from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Item(Base):
    """物品。归属某角色(owner)或放置于某地点(location)，可有任意结构化状态。

    易主 / 移动 / 状态变化都更新本行并追加一条 WorldEvent。
    """

    __tablename__ = "ais_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # 当前持有者(ais_characters.id)；为空表示无主
    owner_character_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 当前所在地点(ais_locations.id)；与 owner 二选一或并存(放在某人住所)
    location_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 任意结构化状态(耐久、是否上锁、充能等)
    state: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
