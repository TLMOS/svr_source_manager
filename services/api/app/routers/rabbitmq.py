from fastapi import APIRouter, HTTPException, Security
from cryptography.fernet import InvalidToken

from app import crud
from app.security import auth, secrets
from app.clients import source_processor
from app.dependencies import DatabaseDepends


router = APIRouter(
    prefix='/rabbitmq',
    tags=['RabbitMQ'],
)


@router.post(
    '/set_credentials',
    summary='Set RabbitMQ credentials'
)
async def set_credentials(
    db: DatabaseDepends,
    username: str,
    password: str,
    client: auth.Client = Security(auth.get_current_client),
):
    """
    Set RabbitMQ credentials.
    Credentials are encrypted before saving to the database.

    Parameters:
    - username (str): RabbitMQ username
    - password (str): RabbitMQ password
    """
    username = secrets.encrypt(username, client.encryption_key)
    password = secrets.encrypt(password, client.encryption_key)
    await crud.secrets.update(db, 'rabbitmq:username', username, True)
    await crud.secrets.update(db, 'rabbitmq:password', password, True)


@router.post(
    '/startup',
    summary='Start source processing'
)
async def startup(
    db: DatabaseDepends,
    client: auth.Client = Security(auth.get_current_client),
):
    """
    Start RabbitMQ session.

    Parameters:
    - encryption_password (str): Password used to encrypt RabbitMQ credentials

    Raises:
    - HTTPException 400: Source processing already running
    - HTTPException 400: RabbitMQ credentials not found in database
    """
    username = await crud.secrets.read(db, 'rabbitmq:username')
    password = await crud.secrets.read(db, 'rabbitmq:password')
    if username is None or password is None:
        raise HTTPException(
            status_code=400,
            detail='RabbitMQ credentials not found in database'
        )
    try:
        username = secrets.decrypt(username, client.encryption_key)
        password = secrets.decrypt(password, client.encryption_key)
        await source_processor.rabbitmq_startup(username, password)
    except InvalidToken:
        raise HTTPException(
            status_code=400,
            detail='Invalid encryption password'
        )


@router.post(
    '/shutdown',
    summary='Stop RabbitMQ session',
    dependencies=[Security(auth.requires_auth)],
)
async def shutdown():
    """Stop source processing"""
    await source_processor.rabbitmq_shutdown()


@router.get(
    '/is_opened',
    summary='Check if RabbitMQ session is opened',
    response_description='RabbitMQ session status',
    dependencies=[Security(auth.requires_auth)],
)
async def is_opened() -> bool:
    """Check if source processing is running"""
    return await source_processor.rabbitmq_is_opened()
