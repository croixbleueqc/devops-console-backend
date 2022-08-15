from fastapi import APIRouter, Depends, HTTPException, status
from devops_console import crud

from sqlalchemy.orm import Session
from devops_console.api.deps import get_current_user, get_db
from devops_console.schemas import User
from ....schemas.user import UserCreate

router = APIRouter()


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/users/create", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
):
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = crud.user.create(db, obj_in=user_in)

    return user
