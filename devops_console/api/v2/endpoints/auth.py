from datetime import timedelta
from devops_console import crud

from devops_console.api.deps import get_db
from devops_console.core.config import settings
from devops_console.core.security import create_access_token
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter()


@router.post(
    "/token",
    # status_code=status.HTTP_204_NO_CONTENT,
    # response_class=Response,  # https://github.com/tiangolo/fastapi/issues/4939
)
def access_token(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_TTL)
    access_token = create_access_token(
        data={"sub": f"{user.id}"},
        expires_delta=access_token_expires,
    )

    # TODO: add refresh token
    # TODO: remove the cookie? (used with htmx)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.headers["HX-Trigger"] = "reload"

    return {"access_token": access_token, "token_type": "bearer"}
