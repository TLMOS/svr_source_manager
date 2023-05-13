from typing import Any
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    # Service urls
    api_url: str = ''

    # Video settings
    frame_size: tuple[int, int] = (640, 480)
    chunk_duration: float = 60
    chunk_fps: float = 1
    capture_max_retries: int = 5
    capture_retries_interval: float = 0.1
    draw_timestamp: bool = True

    # File system settings
    chunks_dir: Path = Path('./videos/chunks')

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'frame_size':
                return tuple(map(int, raw_val.split('x')))
            return cls.json_loads(raw_val)


settings = Settings()

settings.chunks_dir = settings.chunks_dir.resolve()
settings.chunks_dir.mkdir(parents=True, exist_ok=True)
