from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class RoomParticipant(Base):
    """房间参与者：把一个已有的 Role(人格) 关联进某个房间。"""

    __tablename__ = "ais_comm_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 冗余存一份名字，避免每次都回查 Role 表
    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
