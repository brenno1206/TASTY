from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .business import Business

class BusinessType(db.Model):
    __tablename__ = "business_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(45), nullable=False)
    emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # N:N Relationships
    businesses: Mapped[List["Business"]] = relationship(
        "Business", secondary="business_has_type", back_populates="business_types"
    )
    users: Mapped[List["User"]] = relationship(
        "User", secondary="preferences", back_populates="preferences"
    )

    def __repr__(self) -> str:
        return f"<BusinessType {self.name}>"