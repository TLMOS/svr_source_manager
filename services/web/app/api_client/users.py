from app.api_client.base import Router
from app.schemas import User, UserCreate


route = Router('users')


def forget():
    """
    Forget current user.
    """
    route.request('POST', 'forget')


def me() -> User:
    """
    Get current user.
    """
    return User(**route.request('GET', 'me').json())


def create(user: UserCreate):
    """
    Create new user.
    """
    route.request('POST', 'create', json=user.dict())


def get(id: int) -> User:
    """
    Get user by id.
    """
    return User(**route.request('GET', f'get/{id}').json())


def get_all() -> list[User]:
    """
    Get list of all users.
    """
    return [User(**user) for user in route.request('GET', 'get/all').json()]


def update_password(id: int, password: str):
    """
    Update user password.
    """
    route.request('PUT', 'update/password', id=id, password=password)


def update_max_sources(id: int, max_sources: int):
    """
    Update user max sources.
    """
    route.request('PUT', 'update/max_sources', id=id, max_sources=max_sources)


def delete(id: int):
    """
    Delete user by id.
    """
    route.request('DELETE', 'delete', id=id)
