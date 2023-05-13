from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from common import schemas
from app.database import async_session_factory
from app.config import settings
from app.routers import users, sources, videos
from app import crud, security


tags_metadata = [
    {
        "name": "User management",
        "description": "Manage users."
    },
    {
        "name": "Source management",
        "description": "Manage video sources."
    },
    {
        "name": "Video managment",
        "description": "Retrieve video data and manage video chunks"
    }
]


description = """
Core API for the Security Video Retrieval project.

This API is used to manage users, video sources, retrieve video data and
send it to the processing API.
"""


app = FastAPI(
    title="Security Video Retrieval Core API",
    description=description,
    version="0.1.4",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/mit-license.php"
    },
    openapi_tags=tags_metadata
)


app.include_router(users.router)
app.include_router(sources.router)
app.include_router(videos.router)


@app.on_event("startup")
async def startup():
    """Startup event. Create admin user if needed."""
    if settings.admin_create:
        async with async_session_factory() as session:
            user = await crud.users.read_by_name(
                session,
                settings.admin_username
            )
            if user is None:
                user = schemas.UserCreate(
                    name=settings.admin_username,
                    password=security.get_password_hash(
                        settings.admin_password
                    ),
                    role=schemas.UserRole.ADMIN,
                    max_sources=-1
                )
                await crud.users.create(session, user)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url="/docs")
