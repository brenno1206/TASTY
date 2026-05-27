from typing import List, Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String, Index
from tasty.ext.db import db

if TYPE_CHECKING:
    from .address import Address
    from .business import Business

class User(db.Model):
    pass