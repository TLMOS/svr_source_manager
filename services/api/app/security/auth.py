from typing import Optional, Annotated
from datetime import datetime, timedelta
import time

from fastapi.security.oauth2 import OAuth2, OAuthFlowsModel
from fastapi.security import HTTPBasic
from fastapi.param_functions import Form
from fastapi import HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

from common.config import settings
from app.security import secrets
from app import crud
from app.clients import source_processor
from app.dependencies import DatabaseDepends


class Token(BaseModel):
    """ OAuth2 access token """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """ OAuth2 access token data """
    client_id: str
    encryption_key: str


class Client(BaseModel):
    """ OAuth2 client """
    id: str
    encryption_key: str


class OAuth2ClientCredentials(OAuth2):
    """
    OAuth2 client credentials flow.
    Modelled after OAuth2PasswordBearer.

    Attributes:
    - token_url (str): OAuth2 token URL
    - scopes (dict): OAuth2 scopes
    """

    def __init__(self, tokenUrl: str,
                 scopes: Optional[dict[str, str]] = None):
        """
        Initialize OAuth2 client credentials flow.

        Args:
        - token_url (str): OAuth2 token URL
        - scopes (dict): OAuth2 scopes
        """
        scopes = scopes or {}
        flows = OAuthFlowsModel(
            clientCredentials={
                'tokenUrl': tokenUrl,
                'scopes': scopes,
            },
        )
        super().__init__(
            flows=flows,
            scheme_name='OAuth2 Client Credentials',
            auto_error=True,
        )

    async def __call__(self, request: Request):
        authorization = request.headers.get('Authorization')
        if authorization and len(authorization.split()) == 2:
            scheme, param = authorization.split()
            if scheme.lower() == 'bearer':
                return param
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
            headers={'WWW-Authenticate': 'Bearer'},
        )


class OAuth2ClientCredentialsRequestForm:
    """
    OAuth2 client credentials form, expects client cridentials.
    It is a dependency for the OAuth2 client credentials flow.
    Modeled after OAuth2PasswordRequestForm.

    Attributes:
    - grant_type (str): Grant type, must be client_credentials
    - scope (str): Space-separated list of scopes
    - client_id (str): Client ID
    - client_secret (str): Client secret
    """

    def __init__(
            self,
            grant_type: str = Form(None, regex='^(client_credentials)$'),
            scope: str = Form(''),
            client_id: str = Form(None),
            client_secret: str = Form(None),
    ):
        self.grant_type = grant_type
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Parameters:
    - data (dict): data to encode
    - expires_delta (timedelta): token expiration time

    Returns:
    - str: encoded JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(
        to_encode,
        key=settings.security.secret_key,
        algorithm=settings.security.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode JWT access token.

    Parameters:
    - token (str): encoded JWT access token

    Returns:
    - Optional[TokenData]: decoded JWT access token if valid, None otherwise
    """

    try:
        payload = jwt.decode(
            token=token,
            key=settings.security.secret_key,
            algorithms=[settings.security.jwt_algorithm],
        )
        client_id: str = payload.get('sub')
        if client_id is None:
            return None
        encryption_key = payload.get('encryption_key', None)
        return TokenData(
            client_id=client_id,
            encryption_key=encryption_key,
        )
    except (JWTError, ValidationError):
        return None


oauth2_scheme = OAuth2ClientCredentials(tokenUrl='security/token')
token_scheme = HTTPBasic(auto_error=False)


rabbitmq_last_check = time.time()


async def ensure_rabbitmq_is_opened(db: AsyncSession, encryption_key: str):
    """
    Ensure that RabbitMQ session is opened. Once in defined interval,
    check if RabbitMQ session is opened, and if not, try to open it.

    Parameters:
    - encryption_key (str): encryption key, needed to decrypt RabbitMQ
        credentials, which are stored in the database
    """
    global rabbitmq_last_check
    if time.time() - rabbitmq_last_check < settings.rabbitmq.check_interval:
        return
    if await source_processor.rabbitmq_is_opened():
        return

    sm_name = await crud.secrets.read(db, 'source_manager:name')
    username = await crud.secrets.read(db, 'rabbitmq:username')
    password = await crud.secrets.read(db, 'rabbitmq:password')
    if username and password and sm_name:
        username = secrets.decrypt(username, encryption_key)
        password = secrets.decrypt(password, encryption_key)
        await source_processor.rabbitmq_startup(username, password,
                                                sm_name)


async def requires_auth(
        db: DatabaseDepends,
        token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
        x_is_local: bool = Header(
            default=False,
            description='Allow access without token if request is local',
            alias='X-Is-Local',
            convert_underscores=False,
            include_in_schema=False,
        ),
):
    """
    Dependency for OAuth2 client credentials flow.

    Parameters:
    - token (Optional[str]): Access token, should be provided until
                             x_is_local is set to True.
    - x_is_local (bool): Allow access without token if request is local.
                         This header is removed from all external requests
                         by the reverse proxy (nginx).

    Raises:
    - HTTPException 401: if token is not provided or is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if not x_is_local:
        if token is None:
            raise credentials_exception
        token_data = decode_access_token(token)
        if token_data is None:
            raise credentials_exception
        if not token_data.client_id:
            raise credentials_exception
        await ensure_rabbitmq_is_opened(db, token_data.encryption_key)


async def get_current_client(
        db: DatabaseDepends,
        token: Annotated[str, Depends(oauth2_scheme)]
) -> Client:
    """
    Dependency for OAuth2 client credentials flow.

    Parameters:
    - token (str): JWT Access token

    Raises:
    - HTTPException 401: if token is not provided or is invalid

    Returns:
    - Client: current client
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if token is None:
        raise credentials_exception
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception
    if not token_data.client_id:
        raise credentials_exception
    await ensure_rabbitmq_is_opened(db, token_data.encryption_key)
    return Client(id=token_data.client_id,
                  encryption_key=token_data.encryption_key)
