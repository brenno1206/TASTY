from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from tasty.ext.db import db

class Preference(db.Model):
    """Tabela de associação para o relacionamento muitos-para-muitos entre User e BusinessType, representando as preferências dos usuários em relação aos tipos de estabelecimentos parceiros."""
    __tablename__ = "preferences"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("business_types.id", ondelete="CASCADE"), primary_key=True)