from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from storage.db import Base


class Manuscript(Base):
    """写作层成稿：某世界某章节的小说散文(+摘要)。按 (world_id, chapter_label) 唯一，可覆盖重写。"""

    __tablename__ = "ais_manuscripts"
    __table_args__ = (UniqueConstraint("world_id", "chapter_label", name="uq_manuscript_world_chapter"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    chapter_label: Mapped[str] = mapped_column(String(60), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
