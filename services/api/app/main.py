from fastapi import FastAPI, HTTPException, Security
from fastapi.responses import RedirectResponse

from common.credentials import (
    credentials_loader,
    Credentials,
    CredentialsCreate
)
from app.routers.sources import router as sources_router
from app.routers.videos import router as videos_router
from app.clients import source_processor
from app.security import secrets, auth


tags_metadata = [
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
    version='0.4.1',
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/mit-license.php'
    },
    openapi_tags=tags_metadata,
)


@app.on_event('startup')
async def startup():
    source_processor.session.open()


@app.on_event('shutdown')
async def shutdown():
    await source_processor.session.close()


app.include_router(sources_router)
app.include_router(videos_router)


@app.get('/', include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url='/docs')


@app.get(
    '/is_registered',
    summary='Check if source manager is registered in main API',
)
async def is_registered() -> dict:
    """Check if source manager is registered in main API"""
    return {'is_registered': credentials_loader.is_registered()}


@app.post(
    '/register',
    summary='Register source manager in main API (Search Engine)',
)
async def register(credentials: CredentialsCreate):
    """Register source manager in main API (Search Engine)"""
    if credentials_loader.is_registered():
        raise HTTPException(
            status_code=400,
            detail='Source manager is already registered'
        )
    credentials_loader.credentials = Credentials(
        api_key_hash=secrets.hash(credentials.api_key),
        **credentials.dict()
    )
    try:
        await source_processor.restart()
    except Exception as e:
        credentials_loader.delete()
        raise HTTPException(
            status_code=500,
            detail='Failed to register source manager'
        ) from e


@app.post(
    '/unregister',
    summary='Unregister source manager in main API (Search Engine)',
    dependencies=[Security(auth.requires_auth)]
)
async def unregister():
    """Unregister source manager in main API (Search Engine)"""
    if not credentials_loader.is_registered():
        raise HTTPException(
            status_code=400,
            detail='Source manager is not registered'
        )
    credentials_loader.delete()
    await source_processor.restart()
