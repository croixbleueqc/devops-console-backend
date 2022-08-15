import logging

from sqlalchemy.orm import Session

from devops_console.core.database import Base, SessionLocal

from . import crud
from .core import settings
from .schemas.user import UserCreate


def init_db(db: Session) -> None:
    Base.metadata.create_all(bind=db.get_bind())

    user = crud.user.get_by_email(db, email=settings.superuser.email)
    if not user:
        # create superuser
        user_create = UserCreate(
            email=settings.superuser.email,
            plugin_id="cbq",
            password=settings.superuser.pwd,
            bitbucket_username=settings.superuser.email,
            bitbucket_app_password=settings.superuser.app_passwords.bitbucket_management,
        )
        _ = crud.user.create(db, obj_in=user_create)


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
    logging.info("Database initialized")
