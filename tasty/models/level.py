from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

# ----------------------------------------------------------
# level
# ----------------------------------------------------------
class Level(db.Model):
    __tablename__ = "levels"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(db.String(255))
    status: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Level {self.name}>"