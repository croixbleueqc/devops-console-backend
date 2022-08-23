import logging

from sqlalchemy.orm import Session

from devops_console.core.database import Base, engine

from . import crud
from .core import settings
from .schemas.user import UserCreate


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=engine)

    user = crud.user.get_by_email(db, email=settings.superuser.email)
    if not user:
        # create superuser
        user_create = UserCreate(
            full_name="Admin User",
            email=settings.superuser.email,
            plugin_id="cbq",
            password=settings.superuser.pwd,
            bitbucket_username=settings.superuser.username,
            bitbucket_app_password=settings.superuser.app_passwords.bitbucket_management,
        )
        _ = crud.user.create(db, obj_in=user_create)
    logging.info("Database initialized")
