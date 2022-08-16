from sqlalchemy.orm import Session

from ..core.security import hash_password, verify_password

from ..models import User
from ..schemas import UserCreate, UserUpdate
from .base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def authenticate(self, db: Session, *, email: str, password: str) -> User:
        user = self.get_by_email(db, email=email)
        if not user:
            raise Exception("User not found")
        if not verify_password(password, user.hashed_password):  # type: ignore
            raise Exception("Password does not match")
        return user

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            full_name=obj_in.full_name,
            email=obj_in.email,
            plugin_id=obj_in.plugin_id,
            hashed_password=hash_password(obj_in.password),
            bitbucket_username=obj_in.bitbucket_username,
            bitbucket_app_password=obj_in.bitbucket_app_password,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
