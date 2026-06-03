from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db


class BusinessSwipe(db.Model):
    __tablename__ = "business_swipes"
    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_business_swipe"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    business_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True
    )

    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    super_like: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # relacionamentos opcionais
    user = relationship("User")
    business = relationship("Business")