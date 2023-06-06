from pathlib import Path
import os

from pydantic import (
    BaseModel,
    BaseSettings,
    Field,
    validator,
    ValidationError,
    PostgresDsn,
    HttpUrl,
)


class ApiSettings(BaseModel):
    url: HttpUrl = 'http://api:8000'


class SourceProcessorSettings(BaseModel):
    url: HttpUrl = 'http://source_processor:8000'

    capture_timeout: int = 1
    capture_max_retries: int = 3
    capture_retries_interval: float = 0.1


class SearchEngineSettings(BaseModel):
    url: HttpUrl = 'http://search_engine:8000'


class PostgresSettings(BaseModel):
    dsn: PostgresDsn = ('postgresql+asyncpg://'
                        'postgres:postgres@postgres:5432/postgres')

    @validator('dsn')
    def validate_dsn(cls, v: PostgresDsn):
        if v.scheme == 'postgresql+asyncpg':
            return v
        raise ValidationError('Only postgresql+asyncpg scheme is supported')


class RabbitMQSettings(BaseModel):
    vhost: str = '/'
    check_interval: int = 60

    video_chunks_exchange: str = 'video_chunks'


class SecuritySettings(BaseModel):
    secret_key: str = os.urandom(32)  # Make sure to redefine it in production
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days


class PathsSettings(BaseModel):
    chunks_dir: Path = Path('./video_data/chunks')
    sources_dir: Path = Path('./video_data/sources')
    credentials: Path = Path('./credentials/credentials.json')

    @validator('*')
    def validate_path(cls, v: Path, field: Field):
        if field.name.endswith('_dir'):
            v.mkdir(parents=True, exist_ok=True)
        return v.resolve()


class VideoSettings(BaseModel):
    frame_width: int = 640
    frame_height: int = 480
    frame_size: tuple[int, int] = (frame_width, frame_height)
    chunk_duration: float = 60
    chunk_fps: float = 1
    draw_timestamp: bool = True


class Settings(BaseSettings):
    api: ApiSettings = ApiSettings()
    source_processor: SourceProcessorSettings = SourceProcessorSettings()
    search_engine: SearchEngineSettings = SearchEngineSettings()
    postgres: PostgresSettings = PostgresSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    security: SecuritySettings = SecuritySettings()
    paths: PathsSettings = PathsSettings()
    video: VideoSettings = VideoSettings()

    class Config:
        env_nested_delimiter = '__'


settings = Settings()
