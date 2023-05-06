from typing import Any
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Postgres settings
    pguser: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'postgres'
    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    postgres_url: str = None

    # Authorization settings
    admin_create: bool = True
    admin_username: str = 'admin'
    admin_password: str = 'admin'

    # File system settings
    chunks_dir: Path = Path('./videos/chunks')
    sources_dir: Path = Path('./videos/sources')
    tmp_dir: Path = Path('./tmp')

    # Video settings
    frame_size: tuple[int, int] = (640, 480)
    chunk_duration: float = 60
    chunk_fps: float = 1
    draw_timestamp: bool = True

    class Config:
        secrets_dir = '/run/secrets'

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'frame_size':
                return tuple(map(int, raw_val.split('x')))
            return cls.json_loads(raw_val)


settings = Settings()

settings.chunks_dir = settings.chunks_dir.resolve()
settings.sources_dir = settings.sources_dir.resolve()
settings.tmp_dir = settings.tmp_dir.resolve()
settings.chunks_dir.mkdir(parents=True, exist_ok=True)
settings.sources_dir.mkdir(parents=True, exist_ok=True)
settings.tmp_dir.mkdir(parents=True, exist_ok=True)

if settings.postgres_url is None:
    settings.postgres_url = 'postgresql+asyncpg://{}:{}@{}:{}/{}'.format(
        settings.pguser,
        settings.postgres_password,
        settings.postgres_host,
        settings.postgres_port,
        settings.postgres_db
    )
