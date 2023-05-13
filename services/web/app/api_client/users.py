from flask_login import UserMixin

from common import schemas
from common.schemas import UserCreate
from app.api_client.base import Router


class User(UserMixin, schemas.User):
    """Basic user schema, with login logic mixin"""
    pass


route = Router('users')


def create(user: UserCreate):
    route.request('POST', 'create', json=user.dict())


def verify(name: str, password: str) -> User:
    res = route.request('POST', 'verify',
                        params={'name': name, 'password': password})
    if res.json():
        return User(**res.json())


def get(id: int) -> User:
    return User(**route.request('GET', f'get/{id}').json())


def get_all() -> list[User]:
    return [User(**user) for user in route.request('GET', 'get/all').json()]


def delete(id: int):
    route.request('DELETE', 'delete', params={'id': id})
