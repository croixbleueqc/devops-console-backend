from atlassian.bitbucket import Cloud as BitbucketSession
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from devops_console import models, schemas
from sqlalchemy.orm import Session

from devops_console.api.deps import get_current_user, get_db
from devops_console.api.v2.endpoints import users
from .bitbucket import get_bitbucket_session, get_repositories
from devops_console.templates import templates
from devops_console.core import settings


router = APIRouter()


class Context(dict):
    def __init__(self, request: Request, **kwargs):
        super().__init__(request=request, **kwargs)
        # self.update(prefix=settings.API_V2_STR)


@router.get("/")
async def home(
    request: Request,
    user: models.User = Depends(get_current_user),
):
    if user is None:
        return templates.TemplateResponse("login.html", Context(request=request))
    ctx = Context(request, user=user, repositories=f"{settings.API_V2_STR}/bb/repos")
    return templates.TemplateResponse("index.html", ctx)


@router.get("/login")
def login(request: Request):
    ctx = Context(request, action=f"{settings.API_V2_STR}/token")
    t = templates.TemplateResponse("login.html", ctx)
    t.headers["HX-Refresh"] = "true"

    return t


@router.get("/logout")
def logout(request: Request):
    ctx = Context(request)

    t = templates.TemplateResponse("login.html", ctx)

    t.delete_cookie("access_token")
    t.headers["HX-Refresh"] = "true"

    return t


@router.get("/create-user")
async def create_user(request: Request, user=Depends(get_current_user)):
    ctx = Context(request, action="/create-user")
    return templates.TemplateResponse("fragments/create-user.html", ctx)


@router.post("/create-user")
async def create_user_post(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
    full_name: str = Form(),
    email: str = Form(),
    password: str = Form(),
    plugin_id: str = Form(),
    bitbucket_username: str = Form(),
    bitbucket_app_password: str = Form(),
):
    user_in = schemas.UserCreate(
        full_name=full_name,
        email=EmailStr(email),
        password=password,
        plugin_id=plugin_id,
        bitbucket_username=bitbucket_username,
        bitbucket_app_password=bitbucket_app_password,
    )
    user = users.create_user(db=db, user_in=user_in)

    return RedirectResponse(f"/users/{user.id}")


@router.get("/users")
def read_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    usrs = users.read_users(db=db, current_user=current_user)
    ctx = Context(request, users=usrs)
    return templates.TemplateResponse("fragments/users.html", ctx)


@router.get("/users/{user_id}")
def read_user(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = users.read_user(user_id=user_id, db=db, current_user=current_user)
    ctx = Context(request, user=user)
    return templates.TemplateResponse("fragments/user.html", ctx)
