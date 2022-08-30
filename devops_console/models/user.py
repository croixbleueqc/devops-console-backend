from sqlalchemy import Column, Integer, String

from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    plugin_id = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    bitbucket_username = Column(String, nullable=False)
    bitbucket_app_password = Column(String, nullable=False)
