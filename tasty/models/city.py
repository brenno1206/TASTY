from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

if TYPE_CHECKING:
    from .address import Address

class City(db.Model):
    __tablename__ = "cities"

    __table_args__ = (
        Index("idx_city_name_state_country", "name", "state", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="city")

    def __repr__(self) -> str:
        return f"<City {self.name}{' - ' + self.state if self.state else ''}>"