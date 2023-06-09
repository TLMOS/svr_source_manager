from pathlib import Path

from pydantic import (
    BaseModel,
    BaseSettings,
    Field,
    validator,
    ValidationError,
    PostgresDsn,
    HttpUrl,
    PositiveInt,
    PositiveFloat,
)


class ApiSettings(BaseModel):
    url: HttpUrl = 'http://api:8080'


class SourceProcessorSettings(BaseModel):
    url: HttpUrl = 'http://source_processor:8080'

    capture_timeout: PositiveFloat = 1
    capture_max_retries: PositiveInt = 3
    capture_retries_interval: PositiveFloat = 0.1


class SearchEngineSettings(BaseModel):
    url: HttpUrl = 'http://search_engine:8080'


class PostgresSettings(BaseModel):
    url: PostgresDsn = ('postgresql+asyncpg://'
                        'postgres:postgres@postgres:5432/postgres')

    @validator('url')
    def validate_url(cls, v: PostgresDsn):
        if v.scheme == 'postgresql+asyncpg':
            return v
        raise ValidationError('Only postgresql+asyncpg scheme is supported')


class RabbitMQSettings(BaseModel):
    video_chunks_exchange: str = 'video_chunks'


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
    frame_width: int = Field(640, ge=28, le=1920)
    frame_height: int = Field(480, ge=28, le=1080)
    chunk_duration: float = Field(60, gt=1, le=600)
    chunk_fps: float = Field(1, gt=0, le=60)
    draw_timestamp: bool = True


class Settings(BaseSettings):
    api: ApiSettings = ApiSettings()
    source_processor: SourceProcessorSettings = SourceProcessorSettings()
    search_engine: SearchEngineSettings = SearchEngineSettings()
    postgres: PostgresSettings = PostgresSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    paths: PathsSettings = PathsSettings()
    video: VideoSettings = VideoSettings()

    class Config:
        env_nested_delimiter = '__'


settings = Settings()
