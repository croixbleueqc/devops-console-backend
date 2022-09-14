from datetime import datetime

from devops_console import crud, schemas
from fastapi import Depends, HTTPException, status
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.exceptions import InvalidAuth
from fastapi_azure_auth.user import User as AzureUser
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..core.security import (
    OAuth2PasswordCookie,
    credentials_exception,
)

# -----------------------------------------------------------------------------------
# azure deps
# -----------------------------------------------------------------------------------

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    scopes={
        f"api://{settings.APP_CLIENT_ID}/user_impersonation": "user_impersonation",
    },
    tenant_id=settings.TENANT_ID,
)


async def validate_is_admin_user(user: AzureUser = Depends(azure_scheme)) -> None:
    """
    Validate that the user is an admin user.
    """
    if "AdminUser" not in user.roles:
        raise InvalidAuth("User is not an AdminUser")


# -----------------------------------------------------------------------------------
# oauth2 deps
# -----------------------------------------------------------------------------------

# !!! REMOVE/CHANGE THIS; THE REST OF THIS FILE IS FOR DEVELOPMENT PURPOSES ONLY !!!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordCookie(tokenUrl=f"{settings.API_V2_STR}/token")


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    if settings.ENVIRONMENT == "development" and settings.DEV_AUTH and token == settings.DEV_TOKEN:
        superuser = crud.user.get_by_email(db, email=settings.superuser.email)
        if superuser:
            return superuser

    token_data = validate_token(token)

    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise credentials_exception

    return user


def validate_token(token: str) -> schemas.TokenData:
    """Validate token and return payload."""

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = schemas.TokenData(**payload)
        if token_data.exp < datetime.utcnow().timestamp():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        return token_data
    except (JWTError, ValidationError):
        raise credentials_exception
