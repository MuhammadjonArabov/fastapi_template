from fastapi import APIRouter
from . import user

routers = APIRouter()

routers.include_router(user.router)
