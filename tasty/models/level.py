from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .role import Role

class Level(db.Model):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamento 1:N com Role
    roles: Mapped[List["Role"]] = relationship("Role", back_populates="level")

    def __repr__(self) -> str:
        return f"<Level {self.name}>"