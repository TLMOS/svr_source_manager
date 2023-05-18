from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers.security import router as security_router
from app.routers.sources import router as sources_router
from app.routers.videos import router as videos_router
from app.routers.exposed import router as exposed_router
from app.config import settings
from app import crud, security
from app.database import async_session_factory


tags_metadata = [
    {
        "name": "Security",
        "description": "Verify Web-UI user credentials, generate tokens."
    },
    {
        "name": "Source management",
        "description": "Manage video sources."
    },
    {
        "name": "Video managment",
        "description": "Retrieve video data and manage video chunks"
    },
    {
        "name": "Exposed API",
        "description": """API accessible outside of the local network.
            Get frames, chunks and segments from stored video data.
            Requires token authentication.
            """
    }
]


description = """
Core API for the Source Management Application in the SVR project.

This API is used to video sources, retrieve video data and
send it to the processing API.
"""


app = FastAPI(
    title="Security Video Retrieval Core API",
    description=description,
    version="0.2.1",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/mit-license.php"
    },
    openapi_tags=tags_metadata
)


@app.on_event("startup")
async def startup():
    async with async_session_factory() as session:
        secret_db = await crud.secrets.read_by_name(session, 'web_ui_password')
        if secret_db.value is None:
            password = settings.default_web_ui_password
            password = security.get_secret_hash(password)
            await crud.secrets.update_value(
                session, 'web_ui_password', password
            )


app.include_router(security_router)
app.include_router(sources_router)
app.include_router(videos_router)
app.include_router(exposed_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url="/docs")
