from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Relationship(Base):
    """角色间的**有向**关系（A→B 与 B→A 各一条，可不对称）。

    这是「实际」的关系状态(好感度/类型)。某角色对关系的**主观误判**另放在 Belief。
    """

    __tablename__ = "ais_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    to_character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # friend / rival / lover / family / stranger / enemy ...
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="stranger")
    # 好感度 -100 ~ 100
    affinity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
