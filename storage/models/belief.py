from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Belief(Base):
    """主观认知：某角色(holder)对某对象的认知内容，**可能与客观真相不符**。

    这是「主观认知 + 客观真相」分层里的主观层，支撑误解、秘密、欺骗、认知成长。
    客观真相在 Character/Relationship/Item/WorldEvent 等实体里。
    """

    __tablename__ = "ais_beliefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 持有这条认知的角色
    holder_character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 认知对象类型：character / item / location / event / world / fact
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 认知对象 id(指向对应表)；subject_type=fact/world 时可为空
    subject_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # 认知内容("我以为他已经死了" / "这把钥匙能开地窖")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 置信度 0~100
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    # 该认知是否与客观真相相符(可空=未判定)；便于制造/检测误解
    is_true: Mapped[bool] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
