from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer
from tasty.ext.db import db

class BusinessOwner(db.Model):
    __tablename__ = "business_owners"
    __table_args__ = {'extend_existing': True}

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)