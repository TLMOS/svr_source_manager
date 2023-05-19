from common.schemas import Source
from app.clients.core_api.main import session


def create_from_url(name: str, url: str) -> dict:
    return session.post('sources/create/url',
                        params={'name': name, 'url': url}).json()


def creare_from_file(name: str, file_name: str, content: bytes) -> dict:
    return session.post('sources/create/file',
                        params={'name': name},
                        files={'file': (file_name, content)}).json()


def get(id: int) -> Source:
    source = session.get(f'sources/get/{id}').json()
    return Source(**source)


def get_all() -> list[Source]:
    sources = session.get('sources/get/all').json()
    return [Source(**source) for source in sources]


def get_time_coverage(id: int) -> list[tuple[float, float]]:
    return session.get('sources/get/time_coverage', params={'id': id}).json()


def start(id: int):
    session.put('sources/start', params={'id': id})


def pause(id: int):
    session.put('sources/pause', params={'id': id})


def finish(id: int):
    session.put('sources/finish', params={'id': id})


def delete(id: int):
    session.delete('sources/delete', params={'id': id})
