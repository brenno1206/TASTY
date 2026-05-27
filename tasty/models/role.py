from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from tasty.ext.db import db

if TYPE_CHECKING:
    from .level import Level
    from .user import User

class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, index=True)
    
    # FK para Level
    level_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, 
        ForeignKey("levels.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relacionamentos
    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="roles")
    users: Mapped[List["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"