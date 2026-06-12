from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .level import Level
    from .user import User

class Role(db.Model):
    """Modelo de Role, representando as permissões associadas a cada nível de acesso (Level) dentro do sistema, permitindo a definição de diferentes papéis e suas respectivas permissões para os usuários."""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    
    level_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        ForeignKey("levels.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )

    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="roles")
    users: Mapped[List["User"]] = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"