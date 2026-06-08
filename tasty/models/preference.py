from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from tasty.ext.db import db

class Preference(db.Model):
    __tablename__ = "preferences"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("business_types.id", ondelete="CASCADE"), primary_key=True)