from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class CommonKnowledge(Base):
    """世界常识：对世界里**所有** agent 都可见的公共知识条目。

    与 Worldview(整体世界设定散文) 互补——这里是可逐条增删的离散常识点。
    """

    __tablename__ = "ais_common_knowledge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
