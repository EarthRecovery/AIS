from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class WorldSnapshot(Base):
    """世界全量快照：每次「每日结算」前拍一张，用于回退一天。

    state 里存该世界所有状态表的行（角色/心智/记忆/关系/物品/地点/能力/
    常识/场景 + 世界与世界观的标量字段 + 结算前的最大事件 id），回退时整体恢复。
    """

    __tablename__ = "ais_world_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 结算前的世界内时间标签（人类可读，便于在 UI 上展示"回退到哪一天"）
    day_label: Mapped[str] = mapped_column(String(50), nullable=True)
    state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
