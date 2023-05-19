from app.clients.core_api.main import session


def get_last_frame(source_id: int) -> bytes:
    return session.get('videos/frames/get/last',
                       params={'source_id': source_id}).content
