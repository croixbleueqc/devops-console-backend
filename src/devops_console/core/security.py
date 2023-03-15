# from datetime import datetime, timedelta

# from fastapi import Request, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import jwt
# from passlib.context import CryptContext


# from .config import settings

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_TTL)
#     to_encode |= {"exp": expire.timestamp()}
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

#     return encoded_jwt


# credentials_exception = HTTPException(
#     status_code=status.HTTP_401_UNAUTHORIZED,
#     detail="Could not validate credentials",
#     headers={"WWW-Authenticate": "Bearer"},
# )


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# class OAuth2PasswordCookie(OAuth2PasswordBearer):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#     @property
#     def token_name(self) -> str:
#         return "access_token"

#     async def __call__(self, request: Request) -> str | None:
#         # header supercedes cookie
#         if request.headers.get("Authorization"):
#             return await super().__call__(request)
#         token = request.cookies.get(self.token_name)
#         if not token:
#             raise credentials_exception

#         return token
