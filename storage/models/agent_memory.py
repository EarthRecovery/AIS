from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class AgentMemory(Base):
    """角色私有记忆 / 知识库：每个角色一份，互相不可见，随剧情演化。

    统一承载多种认知（kind 区分），把原 Belief 并入为 kind='belief'：
      memory      经历/记得的事
      observation 当场观察到的
      fact        获知的事实/知识
      belief      对某对象的主观看法(可错, 带 subject/confidence/is_true)
      relationship 对某角色关系的私人记录

    由「记录官 Keeper」在场景推进后写入。
    """

    __tablename__ = "ais_agent_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # 记忆归属的角色(ais_characters.id)
    character_id: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="memory")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # belief/relationship 类指向的对象
    subject_type: Mapped[str] = mapped_column(String(20), nullable=True)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # belief 语义：置信度 / 是否与客观真相相符(可空=未判定)
    confidence: Mapped[int] = mapped_column(Integer, nullable=True)
    is_true: Mapped[bool] = mapped_column(Boolean, nullable=True)
    # 来源场景；重要度用于检索/遗忘
    source_scene_id: Mapped[int] = mapped_column(Integer, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 是否已被沉淀进角色的长期自我认知(self_summary)，沉淀后不再单独注入 prompt
    consolidated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
