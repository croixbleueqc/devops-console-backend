from fastapi import APIRouter, Depends, Request

from devops_console.api.deps import get_current_user
from devops_console.templates import templates
from devops_console.core import settings


router = APIRouter()


@router.get("/")
async def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "target": f"{settings.API_V2_STR}/token"}
    )
