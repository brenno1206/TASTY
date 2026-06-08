from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, ForeignKey, DateTime, Boolean, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .business import Business

class BusinessSwipe(db.Model):
    __tablename__ = "business_swipes"
    
    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_business_swipe"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=False
    )

    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    super_like: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relacionamentos estritos e bidirecionais mapeados
    user: Mapped["User"] = relationship("User", back_populates="swipes")
    business: Mapped["Business"] = relationship("Business", back_populates="swipes")

    def __repr__(self) -> str:
        return f"<BusinessSwipe User: {self.user_id} -> Business: {self.business_id} Liked: {self.liked}>"