from pathlib import Path

from pydantic import BaseSettings


basedir = Path(__file__).parent.parent.absolute()


class Settings(BaseSettings):
    # Postgres settings
    pguser: str = 'postgres'
    postgres_password: str = 'postgres'
    postgres_db: str = 'postgres'
    postgres_host: str = 'postgres'
    postgres_port: int = 5432
    postgres_url: str = None

    # Service urls
    source_processor_url: str

    # Authorization settings
    admin_create: bool = True
    admin_username: str = 'admin'
    admin_password: str = 'admin'

    # File system settings
    chunks_dir: Path = basedir / 'videos/chunks'
    sources_dir: Path = basedir / 'videos/sources'
    tmp_dir: Path = Path('./tmp')


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
