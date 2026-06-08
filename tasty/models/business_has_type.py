from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from tasty.ext.db import db

class BusinessHasType(db.Model):
    __tablename__ = "business_has_type"

    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)
    business_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("business_types.id", ondelete="CASCADE"), primary_key=True)