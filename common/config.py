from pathlib import Path
import os

from pydantic import BaseModel, BaseSettings


basedir = Path(__file__).parent.parent.absolute()


class ApiSettings(BaseModel):
    url: str = ''


class SourceProcessorSettings(BaseModel):
    url: str = ''


class RabbitMQSettings(BaseModel):
    host: str = 'rabbitmq'
    port: int = 5672
    vhost: str = '/'
    exchange: str = 'video_chunks'
    check_interval: int = 60


class SecuritySettings(BaseModel):
    secret_key: str = os.urandom(32)  # Make sure to redefine it in production
    jwt_algorithm: str = 'HS256'
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days


class PathsSettings(BaseModel):
    chunks_dir: Path = basedir / 'videos/chunks'
    sources_dir: Path = basedir / 'videos/sources'
    tmp_dir: Path = Path('./tmp')


class VideoSettings(BaseModel):
    frame_width: int = 640
    frame_height: int = 480
    frame_size: tuple[int, int] = (frame_width, frame_height)
    chunk_duration: float = 60
    chunk_fps: float = 1
    capture_timeout: int = 1
    capture_max_retries: int = 3
    capture_retries_interval: float = 0.1
    draw_timestamp: bool = True


class Settings(BaseSettings):
    api: ApiSettings = ApiSettings()
    source_processor: SourceProcessorSettings = SourceProcessorSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    security: SecuritySettings = SecuritySettings()
    paths: PathsSettings = PathsSettings()
    video: VideoSettings = VideoSettings()

    # Postgres settings, cannot be enveloped in a separate class, because
    # they are also used by Postgres container
    pguser: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'postgres'
    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    postgres_url: str = None

    class Config:
        env_nested_delimiter = '__'


settings = Settings()


# Resolve paths
settings.paths.chunks_dir = settings.paths.chunks_dir.resolve()
settings.paths.sources_dir = settings.paths.sources_dir.resolve()
settings.paths.tmp_dir = settings.paths.tmp_dir.resolve()
settings.paths.chunks_dir.mkdir(parents=True, exist_ok=True)
settings.paths.sources_dir.mkdir(parents=True, exist_ok=True)
settings.paths.tmp_dir.mkdir(parents=True, exist_ok=True)


# Resolve Postgres URL
if settings.postgres_url is None:
    settings.postgres_url = 'postgresql+asyncpg://{}:{}@{}:{}/{}'.format(
        settings.pguser,
        settings.postgres_password,
        settings.postgres_host,
        settings.postgres_port,
        settings.postgres_db
    )
