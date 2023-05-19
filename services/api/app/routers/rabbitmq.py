from fastapi import APIRouter, HTTPException
from cryptography.fernet import InvalidToken

from app import crud, security
from app.clients import source_processor
from app.dependencies import SessionDep


router = APIRouter(
    prefix='/rabbitmq',
    tags=['RabbitMQ']
)


@router.post(
    '/set_credentials',
    summary='Set RabbitMQ credentials'
)
async def set_credentials(session: SessionDep, username: str,
                          password: str, encryption_password: str):
    """
    Set RabbitMQ credentials.
    Credentials are encrypted before saving to the database.

    Parameters:
    - username (str): RabbitMQ username
    - password (str): RabbitMQ password
    """
    username = security.encrypt_secret(username, encryption_password)
    password = security.encrypt_secret(password, encryption_password)
    await crud.secrets.update(session, 'rabbitmq_username', username)
    await crud.secrets.update(session, 'rabbitmq_password', password)


@router.post(
    '/startup',
    summary='Start source processing'
)
async def startup(session: SessionDep, encryption_password: str):
    """
    Start RabbitMQ session.

    Parameters:
    - encryption_password (str): Password used to encrypt RabbitMQ credentials

    Raises:
    - HTTPException 400: Source processing already running
    - HTTPException 400: RabbitMQ credentials not found in database
    """
    username = await crud.secrets.read(session, 'rabbitmq_username')
    password = await crud.secrets.read(session, 'rabbitmq_password')
    if username is None or password is None:
        raise HTTPException(
            status_code=400,
            detail='RabbitMQ credentials not found in database'
        )
    try:
        username = security.decrypt_secret(username, encryption_password)
        password = security.decrypt_secret(password, encryption_password)
        await source_processor.rabbitmq_startup(username, password)
    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail='Invalid encryption password'
        )


@router.post(
    '/shutdown',
    summary='Stop RabbitMQ session'
)
async def shutdown():
    """Stop source processing"""
    await source_processor.rabbitmq_shutdown()


@router.get(
    '/is_opened',
    summary='Check if RabbitMQ session is opened',
    response_description='RabbitMQ session status'
)
async def is_opened() -> bool:
    """Check if source processing is running"""
    return await source_processor.rabbitmq_is_opened()
