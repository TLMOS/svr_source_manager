from typing import Optional
import json

from pydantic import BaseModel

from common.config import settings


class RabbitMQCredentials(BaseModel):
    host: str
    port: int
    virtual_host: str
    username: str
    password: str


class SearchEngineCredentials(BaseModel):
    client_id: str
    auth_token: str


class CredentialsBase(BaseModel):
    search_engine: SearchEngineCredentials


class CredentialsCreate(CredentialsBase):
    api_key: str


class Credentials(CredentialsBase):
    api_key_hash: str


class CredentialsLoader:
    """
    Wrapper for client credentials. Loads data from file on first access.

    Parameters:
    - wait_for_file (bool): if True, will wait for file to appear on load
    """

    def __init__(self):
        self._credentials: Optional[Credentials] = None

    def is_registered(self) -> bool:
        """
        Check if client is registered in the search engine.
        If credentials file exists, client considered registered.
        """
        if self._credentials:
            return True
        return settings.paths.credentials.exists()

    def load(self):
        """Force load data from file"""
        if not settings.paths.credentials.exists():
            raise FileNotFoundError((
                'Credentials file not found, most likely source manager '
                'is not registered in the search engine.'
            ))
        with settings.paths.credentials.open('r') as f:
            credentials = json.load(f)
        self._credentials = Credentials(**credentials)

    def save(self):
        """Save data to file"""
        with settings.paths.credentials.open('w') as f:
            json.dump(self.credentials.dict(), f, indent=4)

    def delete(self):
        """Delete credentials file"""
        settings.paths.credentials.unlink()
        self._credentials = None

    @property
    def credentials(self) -> Credentials:
        if self._credentials is None:
            self.load()
        return self._credentials

    @credentials.setter
    def credentials(self, data: Credentials):
        self._credentials = data
        self.save()


credentials_loader = CredentialsLoader()
