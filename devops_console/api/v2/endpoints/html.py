from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from pydantic import EmailStr
from devops_console import models, schemas
from sqlalchemy.orm import Session

from devops_console.api.deps import get_current_user, get_db
from devops_console.api.v2.endpoints import users
from devops_console.api.v2.endpoints.bitbucket import get_bitbucket_session
from devops_console.clients import CoreClient
from devops_console.templates import templates
from devops_console.core import settings

client = CoreClient().sccs
router = APIRouter()


class Context(dict):
    def __init__(self, request: Request, **kwargs):
        super().__init__(request=request, **kwargs)
        # self.update(prefix=settings.API_V2_STR)


@router.get("/")
async def index(
    request: Request,
    user: models.User = Depends(get_current_user),
):
    ctx = Context(request, user=user)
    return templates.TemplateResponse("index.html", ctx)


@router.get("/login")
def login(request: Request):
    ctx = Context(request, action=f"{settings.API_V2_STR}/token")
    t = templates.TemplateResponse("index.html", ctx)
    t.headers["HX-Refresh"] = "true"

    return t


@router.get("/home")
def home(request: Request, user: models.User = Depends(get_current_user)):
    ctx = Context(request, user=user, action=f"{settings.API_V2_STR}/token")
    return templates.TemplateResponse("fragments/home.html", ctx)


@router.get("/logout")
def logout(request: Request):
    ctx = Context(request)

    t = templates.TemplateResponse("index.html", ctx)

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


@router.get("/repo/")
async def read_repo(request: Request, repo_name: str):
    ctx = Context(request, name=repo_name)
    return templates.TemplateResponse("fragments/repo.html", ctx)


@router.get("/repo/{repo_name}")
async def read_repo_details(
    request: Request, repo_name: str, bitbucket_session=Depends(get_bitbucket_session)
):
    plugin_id, session = bitbucket_session
    repo = await client.get_repository(
        plugin_id=plugin_id, session=session, repository=repo_name
    )
    ctx = Context(request, repo=repo)
    return templates.TemplateResponse("fragments/repo-details.html", ctx)


@router.get("/repo-cd/{repo_name}")
async def read_repo_cd(
    request: Request, repo_name: str, bitbucket_session=Depends(get_bitbucket_session)
):
    plugin_id, session = bitbucket_session
    environment_cfgs = await client.get_continuous_deployment_config(
        plugin_id=plugin_id, session=session, repository=repo_name
    )

    ctx = Context(request, envs=environment_cfgs)
    return templates.TemplateResponse("fragments/repo-cd.html", ctx)


@router.get("/repos-options")
async def read_repos(
    request: Request,
    bitbucket_session=Depends(get_bitbucket_session),
):
    plugin_id, session = bitbucket_session
    repos = await client.get_repositories(session=session, plugin_id=plugin_id)

    ctx = Context(request, repos=repos)

    return templates.TemplateResponse("fragments/repos-options.html", ctx)
