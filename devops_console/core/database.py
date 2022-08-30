from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from .config import settings

engine = create_engine(
    settings.DATABASE_URI,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# check_same_thread=False is necessary for sqlite

SessionLocal = sessionmaker(engine)


Base = declarative_base()
