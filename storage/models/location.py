from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Location(Base):
    """地点。住所(residence)是 type='residence' 的地点；支持嵌套(parent)。"""

    __tablename__ = "ais_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # residence(住所) / public / landmark / region ...
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="public")
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # 上级地点(房间属于建筑、建筑属于城区)
    parent_location_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
