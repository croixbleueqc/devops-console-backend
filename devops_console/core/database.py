from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker

from .config import settings

engine = create_engine(settings.DATABASE_URI, connect_args={"check_same_thread": False})
# check_same_thread=False is necessary for sqlite

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@as_declarative()
class Base:
    id: Any
    __name__: str
    # generate table name automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
