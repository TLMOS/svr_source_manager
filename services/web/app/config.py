from pathlib import Path
from pydantic import BaseSettings


basedir = Path(__file__).parent.parent.absolute()


class Settings(BaseSettings):
    # Flask settings
    SECRET_KEY: str
    MAX_CONTENT_LENGTH: int = 1024 * 1024 * 200
    UPLOAD_EXTENSIONS: list[str] = ['.jpg', '.png', '.mp4', '.avi']

    # Service urls
    api_url: str

    # Filesystem settings
    static_folder = (basedir / 'static')
    media_folder = (basedir / 'media')


settings = Settings()

settings.static_folder = settings.static_folder.resolve().absolute()
settings.media_folder = settings.media_folder.resolve().absolute()
settings.static_folder.mkdir(exist_ok=True)
settings.media_folder.mkdir(exist_ok=True)
