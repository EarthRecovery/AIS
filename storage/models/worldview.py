from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Worldview(Base):
    """世界观设定。分两层：

    - description / rules：**公共可知**层，所有在场 agent 都能看到、会注入 prompt。
    - background：**完整背景设定（世界观圣经）**，仅作者可见、用于整理思路，
      绝不整段注入给任何 agent；角色只通过各自私有记忆(AgentMemory)知道其中片段。
    """

    __tablename__ = "ais_worldviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 公共可知：世界概况（地点、时代、阵营、基调等）—— 所有 agent 可见
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # 公共可知：世界规则 / 约束（魔法体系、禁忌、物理法则等）—— 所有 agent 可见
    rules: Mapped[str] = mapped_column(Text, nullable=True)
    # 完整背景设定：仅作者可见、用于整理思路，不注入给 agent（角色只知片段）
    background: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
