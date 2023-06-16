from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from common.schemas import Source, VideoChunk
from common.credentials import credentials_loader
from app.clients import rabbitmq, search_engine
from app.video_processing import SourceProcessor


description = """
Source processing service.
Keeps a list of active sources and process them asynchronously.

Source processing steps:
- Get frames from source url
- Save frames to disk as video chunks
- Create database records for video chunks
- Send video chunks to RabbitMQ queue
"""


app = FastAPI(
    title='SVR Source Processor API',
    description=description,
    version='0.4.1',
    license_info={
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/mit-license.php'
    }
)


source_processor = SourceProcessor()


@app.on_event('startup')
async def on_startup():
    if credentials_loader.is_registered():
        rmq_credentials = search_engine.get_rabbitmq_credentials()
        rabbitmq.session.set_connection_params(**rmq_credentials.dict())
        rabbitmq.session.open()
        source_processor.startup()


@app.on_event('shutdown')
async def on_shutdown():
    source_processor.shutdown()
    if rabbitmq.session.is_opened:
        rabbitmq.session.close()


@app.get('/', include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url='/docs')


@app.post(
    '/restart',
    summary='Restart source processor'
)
async def restart():
    """Restart source processor. Will also reload manager credentials."""
    await on_shutdown()
    await on_startup()


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
    source_processor.remove(source_id)


@app.post(
    '/publish',
    summary='Publish video chunk to RabbitMQ queue'
)
async def publish(chunk: VideoChunk):
    """
    Publish video chunk to RabbitMQ processing queue.

    Args:
    - chunk (models.VideoChunk): video chunk to publish
    """
    rabbitmq.publish_video_chunk(chunk)
