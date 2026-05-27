from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, Index
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .business import Business
    from .city import City

# ----------------------------------------------------------
# Adress
# ----------------------------------------------------------
class Address(db.Model):
    __tablename__ = "address"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    road: Mapped[Optional[str]] = mapped_column(String(100))
    number: Mapped[Optional[int]] = mapped_column(Integer)
    district: Mapped[Optional[str]] = mapped_column(String(100))
    zipcode: Mapped[Optional[str]] = mapped_column(String(15))

    # FK
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # FK
    business_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # FK
    city_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="SET NULL"),
        nullable=False
    )

    # Relacionamentos
    user: Mapped[Optional["User"]] = relationship("User", back_populates="addresses")
    business: Mapped[Optional["Business"]] = relationship("Business", back_populates="address")
    city: Mapped["City"] = relationship("City", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address {self.road}, {self.number} - {self.district}>"