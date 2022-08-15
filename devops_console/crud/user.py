from sqlalchemy.orm import Session

from ..core.security import verify_password

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


user = CRUDUser(User)
