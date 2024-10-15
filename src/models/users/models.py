from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Column
from sqlalchemy.types import Boolean, String

from ...database import Base
from ..metadatas import Metadata  # * Never remove this import.


class User(Base):

    __tablename__: str = "users"
    __allow_unmapped__ = True

    username: Column = Column(String(64), unique=True)
    admin: Column = Column(Boolean, default=False, nullable=True)
    metadatas = relationship("Metadata", backref="user")

    def __repr__(self) -> str:
        return f'<User "{self.username}">'
