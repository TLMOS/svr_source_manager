from app.clients.core_api.main import session


def verify_password(password: str) -> bool:
    return session.get('security/verify_web_ui_password',
                       params={'password': password}).json()


def update_password(password: str):
    session.put('security/update_web_ui_password',
                params={'password': password})


def update_token() -> str:
    return session.put('security/update_token').json()['token']


def invalidate_token():
    session.delete('security/invalidate_token')
