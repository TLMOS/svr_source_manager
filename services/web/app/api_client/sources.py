from app.api_client.base import Router
from app.schemas import Source, SOURCE_STATUS_TO_STR


route = Router('sources', authorized=True)


def create_from_url(name: str, url: str) -> dict:
    return route.request('POST', 'create/url',
                         params={'name': name, 'url': url}).json()


def creare_from_file(name: str, file: bytes) -> dict:
    return route.request('POST', 'create/file',
                         params={'name': name, 'file': file}).json()


def get(id: int) -> Source:
    source = Source(**route.request('GET', f'get/{id}').json())
    source.status = SOURCE_STATUS_TO_STR[source.status_code]
    return source


def get_all() -> list[Source]:
    sources = route.request('GET', 'get/all').json()
    sources = [Source(**source) for source in sources]
    for source in sources:
        source.status = SOURCE_STATUS_TO_STR[source.status_code]
    return sources


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
