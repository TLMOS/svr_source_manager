from typing import Optional
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security import HTTPBasicCredentials

from common.config import settings
from app import crud
from app.security import auth, secrets
from app.dependencies import DatabaseDepends
from app.security.auth import (
    OAuth2ClientCredentialsRequestForm,
    Client,
    Token,
    token_scheme
)

router = APIRouter(
    prefix='/security',
    tags=['Security'],
)


@router.post(
    '/token',
    include_in_schema=False,
    summary='Get OAuth2 access token',
    response_model=auth.Token
)
async def login(
    db: DatabaseDepends,
    form_data: OAuth2ClientCredentialsRequestForm = Depends(),
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(token_scheme),
) -> auth.Token:
    """
    Get OAuth2 access token.

    Does not check the validity of the client_id in any way.
    Authentication is performed solely by client_secret.
    Client_id is used only to identify the client.

    If client_secret is not found in the database, login can be performed
    with the an empty client_secret.

    Encryption key is used to encrypt sensitive data in the database,
    such as RabbitMQ credentials.
    If encryption key is not specified during login,
    it will be generated and saved in the database.

    Raises:
    - HTTPException 401: Incorrect client_id or client_secret

    Returns:
    - dict: OAuth2 access token
    """

    failed_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect client_id or client_secret',
    )
    if form_data.client_id and form_data.client_secret:
        client_id = form_data.client_id
        client_secret = form_data.client_secret
    elif basic_credentials:
        client_id = basic_credentials.username
        client_secret = basic_credentials.password
    else:
        raise failed_auth

    secret_hash = await crud.secrets.read(db, 'api:client_secret')
    if secret_hash:
        if not secrets.verify(client_secret, secret_hash):
            raise failed_auth
    elif client_secret != '':
        raise failed_auth

    encryption_key = await crud.secrets.read(db, 'api:encryption_key')
    if encryption_key:
        encryption_key = secrets.decrypt(encryption_key, client_secret)
    else:
        encryption_key = str(uuid.uuid4())
        await crud.secrets.update(
            db,
            name='api:encryption_key',
            value=secrets.encrypt(encryption_key, client_secret),
        )

    access_token_expires = timedelta(
        minutes=settings.security.jwt_access_token_expire_minutes
    )
    access_token = auth.create_access_token(
        data={'sub': client_id, 'encryption_key': encryption_key},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type='bearer')


@router.put(
    '/update_client_secret',
    summary='Update client secret (password)'
)
async def update_client_secret(
    db: DatabaseDepends,
    client: Client = Security(auth.get_current_client),
) -> str:
    """
    Generate new client secret. Old secret will be invalidated.
    Also generates new encryption key and re-encrypts all sensitive data.

    Returns:
    - dict: New client secret
    """
    client_secret = str(uuid.uuid4())
    client_secret_hash = secrets.hash(client_secret)
    await crud.secrets.update(db, 'api:client_secret', client_secret_hash)

    old_encryption_key = client.encryption_key
    encryption_key = str(uuid.uuid4())
    encrypted_secrets = await crud.secrets.read_all_encrypted(db)
    for secret in encrypted_secrets:
        decrypted_secret = secrets.decrypt(secret.value, old_encryption_key)
        encrypted_secret = secrets.encrypt(decrypted_secret, encryption_key)
        await crud.secrets.update(db, secret.name, encrypted_secret)
    encryption_key = secrets.encrypt(encryption_key, client_secret)
    await crud.secrets.update(db, 'api:encryption_key', encryption_key)
    return client_secret


@router.delete(
    '/invalidate_client_secret',
    summary='Invalidate client secret (password)',
)
async def invalidate_client_secret(
    db: DatabaseDepends,
    client: Client = Security(auth.get_current_client),
):
    """
    Invalidate client secret. Client will be able to access API without
    providing secret, until new secret is set.
    """
    encryption_key = client.encryption_key
    encryption_key = secrets.encrypt(encryption_key, '')
    await crud.secrets.update(db, 'api:client_secret', '')
    await crud.secrets.update(db, 'api:encryption_key', encryption_key)


@router.post(
    '/set_rabbitmq_credentials',
    summary='Set RabbitMQ credentials'
)
async def set_credentials(
    db: DatabaseDepends,
    username: str,
    password: str,
    sm_name: str,
    client: auth.Client = Security(auth.get_current_client),
):
    """
    Set RabbitMQ credentials.
    Credentials are encrypted before saving to the database.

    Parameters:
    - username (str): RabbitMQ username
    - password (str): RabbitMQ password
    - sm_name (str): unique name passed used to identify
        source manager in the post queue data exchange
    """
    username = secrets.encrypt(username, client.encryption_key)
    password = secrets.encrypt(password, client.encryption_key)
    await crud.secrets.update(db, 'rabbitmq:username', username, True)
    await crud.secrets.update(db, 'rabbitmq:password', password, True)
    await crud.secrets.update(db, 'source_manager:name', sm_name)
