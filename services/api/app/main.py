from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers.rabbitmq import router as rabbitmq_router
from app.routers.security import router as security_router
from app.routers.sources import router as sources_router
from app.routers.videos import router as videos_router
from app.routers.exposed import router as exposed_router
from app.config import settings
from app import crud, security
from app.database import async_session_factory
from app.clients import source_processor


tags_metadata = [
    {
        'name': 'Security',
        'description': 'Verify Web-UI user credentials, generate tokens.'
    },
    {
        'name': 'Source management',
        'description': 'Manage video sources.'
    },
    {
        'name': 'Video managment',
        'description': 'Retrieve video data and manage video chunks'
    },
    {
        'name': 'RabbitMQ',
        'description': 'Start and stop RabbitMQ session'
    },
    {
        'name': 'Exposed API',
        'description': """API accessible outside of the local network.
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
    title='SVR Source Manager API',
    description=description,
    version='0.2.3',
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/mit-license.php'
    },
    openapi_tags=tags_metadata
)


@app.on_event('startup')
async def startup():
    async with async_session_factory() as session:
        secret = await crud.secrets.read(session, 'web_ui_password')
        if secret is None:
            password = settings.default_web_ui_password
            password = security.hash_secret(password)
            await crud.secrets.update(
                session, 'web_ui_password', password
            )
    await source_processor.session.startup()


@app.on_event('shutdown')
async def shutdown():
    await source_processor.session.shutdown()


app.include_router(rabbitmq_router)
app.include_router(security_router)
app.include_router(sources_router)
app.include_router(videos_router)
app.include_router(exposed_router)


@app.get('/', include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url='/docs')
