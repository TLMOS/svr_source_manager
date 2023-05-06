import os
from pathlib import Path
from pydantic import BaseModel


basedir = Path(__file__).parent.parent.absolute()


class Settings(BaseModel):
    # Flask settings
    SECRET_KEY: str = os.urandom(24)
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024

    # Core API settings
    api_url: str = 'http://api:8000'

    # Filesystem settings
    static_folder = (basedir / 'static')
    media_folder = (basedir / 'media')


settings = Settings()
settings.static_folder = settings.static_folder.resolve().absolute()
settings.media_folder = settings.media_folder.resolve().absolute()
settings.static_folder.mkdir(exist_ok=True)
settings.media_folder.mkdir(exist_ok=True)
