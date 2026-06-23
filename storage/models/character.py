from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Character(Base):
    """世界中的持久角色实例。

    以现有 Role(ais_roles) 作为基础人格模板，Character 是该人格"活在某个世界里"
    的实例，带可变状态(位置、生死/在场状态)。能力/关系/认知/心智另表建模。
    """

    __tablename__ = "ais_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 基础人格模板(ais_roles.id)；可为空表示纯世界原生角色
    role_id: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    # active / away / dead / ...
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # 当前所在地点(ais_locations.id)
    current_location_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 数值状态（可扩展）：生命值/法力值/体力值等，模拟时每轮由世界裁判更新
    stats: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
