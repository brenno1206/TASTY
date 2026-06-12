from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .user import User
    from .business import Business
    from .city import City

class Address(db.Model):
    """Modelo de Endereço, utilizado para armazenar informações de localização tanto de Usuários quanto de Estabelecimentos Parceiros."""
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    road: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zipcode: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    business_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("businesses.id", ondelete="CASCADE"), index=True, nullable=True
    )
    city_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("cities.id", ondelete="SET NULL"), index=True, nullable=True
    )

    user: Mapped[Optional["User"]] = relationship("User", back_populates="addresses")
    business: Mapped[Optional["Business"]] = relationship("Business", back_populates="addresses")
    city: Mapped[Optional["City"]] = relationship("City", back_populates="addresses")

    def __repr__(self) -> str:
        return f"<Address {self.road}, {self.number} - {self.district}>"