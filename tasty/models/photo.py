from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .business import Business

class Photo(db.Model):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # FK
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relacionamento
    business: Mapped["Business"] = relationship("Business", back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo {self.id} for Business {self.business_id}>"