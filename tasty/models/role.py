from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from tasty.ext.db import db

8 # === Role (papel) ===
class Role(db.Model):
    __tablename__ = "roles"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(30), unique=True, index=True)

    role_associations: Mapped[List[Level]] = relationship(
        ""
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"