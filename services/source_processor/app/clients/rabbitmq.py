import pika
from pika.exceptions import AMQPConnectionError
from fastapi import HTTPException

from common import schemas
from app.config import settings


class PikaSession:
    """
    Wrapper for pika connection to RabbitMQ.

    Attributes:
    - is_opened (bool): True if the connection is opened
    """

    is_opened: bool = False
    _connection: pika.BlockingConnection = None
    _channel: pika.channel.Channel = None

    def startup(self, username: str, password: str):
        try:
            self._connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.rabbitmq_host,
                    port=settings.rabbitmq_port,
                    virtual_host=settings.rabbitmq_vhost,
                    credentials=pika.PlainCredentials(
                        username=username,
                        password=password
                    )
                )
            )
        except AMQPConnectionError as e:
            raise HTTPException(
                status_code=400,
                detail=f'Failed to connect to RabbitMQ: {e}'
            ) from e
        self._channel = self._connection.channel()
        self.is_opened = True

    def shutdown(self):
        self._connection.close()
        self._connection = None
        self._channel = None
        self.is_opened = False

    def publish(self, exchange: str, routing_key: str, body: bytes,
                properties: pika.BasicProperties = None):
        self._channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
            properties=properties
        )


session = PikaSession()


def publish_video_chunk(chunk: schemas.VideoChunkCreate):
    """
    Publish video chunk to RabbitMQ processing queue.

    Args:
    - chunk (models.VideoChunk): video chunk to publish
    """
    with open(chunk.file_path, 'rb') as f:
        content = f.read()

    session.publish(
        exchange=settings.rabbitmq_exchange,
        routing_key='',
        body=content,
        properties=pika.BasicProperties(
            content_type='video/mp4',
            headers={
                'source_id': str(chunk.source_id),
                'start_time': str(chunk.start_time),
                'end_time': str(chunk.end_time)
            }
        )
    )
