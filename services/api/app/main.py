from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers.security import router as security_router
from app.routers.sources import router as sources_router
from app.routers.videos import router as videos_router
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
    version='0.3.1',
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/mit-license.php'
    },
    openapi_tags=tags_metadata,
)


@app.on_event('startup')
async def startup():
    await source_processor.session.startup()


@app.on_event('shutdown')
async def shutdown():
    await source_processor.session.shutdown()


app.include_router(security_router)
app.include_router(sources_router)
app.include_router(videos_router)


@app.get('/', include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url='/docs')
