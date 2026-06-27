from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class LLMLog(Base):
    """每一次大模型 API 调用的明细：完整 prompt + 回复 + 用量。仅管理员可见。"""

    __tablename__ = "ais_llm_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent: Mapped[str] = mapped_column(String(40), nullable=True)    # 来源标签：keeper/narrative/writing/...
    model: Mapped[str] = mapped_column(String(60), nullable=True)
    prompt: Mapped[str] = mapped_column(LONGTEXT, nullable=True)      # 发出去的完整提示词
    response: Mapped[str] = mapped_column(LONGTEXT, nullable=True)    # 模型完整回复
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    ok: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
