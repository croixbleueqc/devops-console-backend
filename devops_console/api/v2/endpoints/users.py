from devops_console import crud, models, schemas
from devops_console.api.deps import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


router = APIRouter()


@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@router.get("/", response_model=list[schemas.User])
def read_users(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    users = crud.user.get_many(db)
    return users


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = crud.user.get(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_in: schemas.UserCreate,
):
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = crud.user.create(db, obj_in=user_in)

    return user
