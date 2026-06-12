from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from tasty.ext.db import db

class BusinessOwner(db.Model):
    """Tabela de associação para o relacionamento muitos-para-muitos entre User e Business, representando os proprietários dos estabelecimentos parceiros."""
    __tablename__ = "business_owners"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)