from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Room(Base):
    """多人格交流房间（一个场景）。

    可独立存在(旧的一次性对话)，也可作为某个持久 World 里的一个「场景/会话」
    (world_id 非空)，此时角色状态/认知/事件挂在 World 层、跨场景延续。
    """

    __tablename__ = "ais_comm_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 所属持久世界(ais_worlds.id)；为空表示独立的一次性房间
    world_id: Mapped[int] = mapped_column(Integer, nullable=True)
    worldview_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 当前场景 / 开场设定（在世界观之下的具体情境）
    scenario: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
