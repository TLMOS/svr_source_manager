from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from common.schemas import Source
from app.clients import rabbitmq
from app.video_processing import SourceProcessor
from app.clients import core_api


description = """
Source processing service.
Keeps a list of active sources and process them asynchronously.

Source processing steps:
- Get frames from source url
- Save frames to disk as video chunks
- Ask core API to create database records for video chunks
- Send video chunks to RabbitMQ queue
"""


app = FastAPI(
    title='SVR Source Processor API',
    description=description,
    version='0.3.1',
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/mit-license.php'
    }
)


source_processor = SourceProcessor()


@app.on_event('startup')
async def on_startup():
    await core_api.session.startup()
    await source_processor.startup()


@app.on_event('shutdown')
async def on_shutdown():
    if source_processor.is_running:
        await source_processor.shutdown()
    if rabbitmq.session.is_opened:
        rabbitmq.session.shutdown()
    if core_api.session.is_opened:
        await core_api.session.shutdown()


@app.get('/', include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url='/docs')


@app.post(
    '/add',
    summary='Add source to processing list'
)
async def add(source: Source):
    """
    Add source to processing list.

    Parameters:
    - id (int): source id
    """
    source_processor.add(source)


@app.delete(
    '/remove',
    summary='Remove source from processing list'
)
async def remove(source_id: int):
    """
    Add source to processing list.

    Parameters:
    - id (int): source id
    """
    await source_processor.remove(source_id)


@app.post(
    '/rabbitmq/startup',
    summary='Start RabbitMQ session'
)
async def rabbitmq_startup(username: str, password: str,
                           sm_name: str):
    """
    Start RabbitMQ session.

    Parameters:
    - username (str): RabbitMQ user
    - password (str): RabbitMQ password
    - sm_name (str): unique name passed to source
        manager by search engine with rabbitmq credentials

    Raises:
    - HTTPException 400: RabbitMQ session is already opened
    """
    if rabbitmq.session.is_opened:
        raise HTTPException(
            status_code=400,
            detail='RabbitMQ session is already opened'
        )
    rabbitmq.session.startup(username, password, sm_name)


@app.post(
    '/rabbitmq/shutdown',
    summary='Stop RabbitMQ session'
)
async def rabbitmq_shutdown():
    """Stop RabbitMQ session"""
    if rabbitmq.session.is_opened:
        rabbitmq.session.shutdown()


@app.get(
    '/rabbitmq/is_opened',
    summary='Check if RabbitMQ session is opened'
)
async def rabbitmq_is_opened() -> bool:
    """Check if RabbitMQ session is opened"""
    return rabbitmq.session.is_opened
