from common.schemas import Source
from app.api_client.base import Router


route = Router('sources', authorized=True)


def create_from_url(name: str, url: str) -> dict:
    return route.request('POST', 'create/url',
                         params={'name': name, 'url': url}).json()


def creare_from_file(name: str, file_name: str, content: bytes) -> dict:
    return route.request('POST', 'create/file',
                         params={'name': name},
                         files={'file': (file_name, content)}).json()


def get(id: int) -> Source:
    return Source(**route.request('GET', f'get/{id}').json())


def get_all() -> list[Source]:
    sources = route.request('GET', 'get/all').json()
    return [Source(**source) for source in sources]


def get_frame(id: int) -> bytes:
    return route.request('GET', 'get/frame', params={'id': id}).content


def get_time_coverage(id: int) -> list[tuple[float, float]]:
    return route.request('GET', 'get/time_coverage', params={'id': id}).json()


def start(id: int):
    route.request('PUT', 'start', params={'id': id})


def pause(id: int):
    route.request('PUT', 'pause', params={'id': id})


def finish(id: int):
    route.request('PUT', 'finish', params={'id': id})


def delete(id: int):
    route.request('DELETE', 'delete', params={'id': id})
