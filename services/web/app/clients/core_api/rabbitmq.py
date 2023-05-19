from app.clients.core_api.main import session


def set_credentials(username: str, password: str, encryption_password: str):
    params = {'username': username, 'password': password,
              'encryption_password': encryption_password}
    session.post('rabbitmq/set_credentials', params=params)


def startup(encryption_password: str):
    params = {'encryption_password': encryption_password}
    session.post('rabbitmq/startup', params=params)


def shutdown():
    session.post('rabbitmq/shutdown')


def is_opened() -> bool:
    return session.get('rabbitmq/is_opened').json()
