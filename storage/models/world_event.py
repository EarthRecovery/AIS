from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class WorldEvent(Base):
    """追加式世界时间线：既记叙事事件，也记一切状态变更(含 before/after)。

    是「可变当前态 + 追加事件日志」里的日志层——任何对关系/物品/认知/心智/
    世界观的更改都在这里留一条，从而支撑长期连续性、回溯与因果追踪。
    """

    __tablename__ = "ais_world_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 触发该事件的场景/会话(ais_comm_rooms.id)，可空(世界级事件)
    scene_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 事件类型：
    #   叙事类   dialogue / action / scene
    #   状态变更 relationship_change / item_transfer / mental_update /
    #            belief_update / ability_change / location_move /
    #            worldview_change / time_advance
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    # 主要行动者(ais_characters.id)，可空
    actor_character_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 人类可读摘要
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    # 结构化细节：状态变更存 {"target":..,"before":..,"after":..}，叙事事件存参与者等
    payload: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    # 事件发生的世界内时间(冗余存，便于按叙事时间排序)
    in_world_time: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
