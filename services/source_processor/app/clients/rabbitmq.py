import pika

from common.config import settings
from common.credentials import credentials_loader
from common.clients.amqp import Session
from common import schemas


session = Session()


def publish_video_chunk(chunk: schemas.VideoChunkCreate):
    """
    Publish video chunk to RabbitMQ processing queue.

    Args:
    - chunk (models.VideoChunk): video chunk to publish
    """
    with open(chunk.file_path, 'rb') as f:
        content = f.read()

    exchange = settings.rabbitmq.video_chunks_exchange
    source_manager_id = credentials_loader.credentials.search_engine.client_id

    session.publish(
        exchange=exchange,
        routing_key='',
        body=content,
        properties=pika.BasicProperties(
            content_type='video/mp4',
            headers={
                'source_manager_id': source_manager_id,
                'source_id': str(chunk.source_id),
                'start_time': str(chunk.start_time),
                'end_time': str(chunk.end_time),
                'farme_count': str(chunk.farme_count),
            }
        )
    )
