from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import register_admin
from app.settings import get_settings
from app.routers import routers

app = FastAPI(
    title=get_settings().title,
    description=get_settings().description,
    version=get_settings().version,
    contact=get_settings().contact,
    license_info=get_settings().license_info,
)

app.include_router(routers)

# set up CORS
cors_list = (get_settings().cors_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_admin(app)