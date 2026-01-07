from sqlalchemy import Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class Role(Base):
    __tablename__ = "ais_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    settings: Mapped[dict] = mapped_column(
        JSON,        
        nullable=True,
        default=dict
    )