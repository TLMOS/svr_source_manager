from app.api_client.base import Router
from app.schemas import Source, SOURCE_STATUS_TO_STR


route = Router('sources')


def create_from_url(name: str, url: str) -> dict:
    """
    Create source from url. By default, the source is paused.
    To start it, use the `start_source` function.

    Args:
        name: Source name.
        url: Url of the source, must be accessible. Supported extensions:
            video: mp4, avi
            video stream: mjpg
            image: png, jpg, jpeg
    """
    return route.request('POST', 'create/url', name=name, url=url).json()


def creare_from_file(name: str, file: bytes) -> dict:
    """
    Create source from file. By default, the source is paused.
    To start it, use the `start_source` function.

    Args:
        name: Source name.
        file: Video file. Supported extensions: mp4, avi
    """
    return route.request('POST', 'create/file', name=name, file=file).json()


def get(id: int) -> Source:
    """
    Get source by id.

    Args:
        id: Source id.
    """
    source = Source(**route.request('GET', f'get/{id}').json())
    source.status = SOURCE_STATUS_TO_STR[source.status_code]
    return source


def get_all() -> list[Source]:
    """
    Get list of all sources.
    """
    from flask import request
    print(request.headers.get('Authorization'))
    sources = route.request('GET', 'get/all').json()
    sources = [Source(**source) for source in sources]
    for source in sources:
        source.status = SOURCE_STATUS_TO_STR[source.status_code]
    return sources


def start(id: int):
    """
    Start source processing in background:
        - Get frames from source url
        - Save frames to disk as video chunks
        - Create database records for video chunks
        - Send video chunks to RabbitMQ queue

    Args:
        id: Source id.
    """
    route.request('PUT', 'start', id=id).json()


def pause(id: int):
    """
    Pause source processing.

    Args:
        id: Source id.
    """
    route.request('PUT', 'pause', id=id)


def finish(id: int):
    """
    Finish source processing. Finished source can't be started again.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Args:
        id: Source id.
    """
    route.request('PUT', 'finish', id=id)


def delete(id: int):
    """
    Delete source. Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.

    Args:
        id: Source id.
    """
    route.request('DELETE', 'delete', id=id)
