from typing import Any
from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    # File system settings
    chunks_dir: Path = Path('./videos/chunks')

    # Core API settings
    api_url: str = 'http://api:8000'

    # Video settings
    frame_size: tuple[int, int] = (640, 480)
    chunk_duration: float = 60
    chunk_fps: float = 1
    draw_timestamp: bool = True

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == 'frame_size':
                return tuple(map(int, raw_val.split('x')))
            return cls.json_loads(raw_val)


settings = Settings()

settings.chunks_dir = settings.chunks_dir.resolve()
settings.chunks_dir.mkdir(parents=True, exist_ok=True)
