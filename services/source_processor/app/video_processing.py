"""
Module for capturing frames from source url and writing them into video chunks
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from pathlib import Path
import time
from datetime import datetime
import requests

import numpy as np
import cv2

from common.constants import SourceStatus
from common.schemas import Source, VideoChunkCreate
from app.config import settings
from app import api_client


VIDEO_EXTENSIONS = ['mp4', 'avi']
STREAM_EXTENSIONS = ['mjpg']
IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg']


class SourceCapture(ABC):
    """Abstract context manager for capturing frames from source"""

    def __init__(self, url: str):
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def has_next(self) -> bool:
        """Check if there is next frame"""
        pass

    @abstractmethod
    async def read(self) -> np.ndarray:
        """Read next frame from source"""
        pass


class ImageCapture(SourceCapture):
    """Context manager for capturing frames from image url"""

    def has_next(self) -> bool:
        return True

    async def read(self) -> np.ndarray:
        # TODO: Mistery of a wierd deadlock
        response = requests.get(self.url, timeout=settings.capture_timeout)
        if self.url.startswith('http') and response.code != 200:
            raise ValueError('Can not read next frame')
        return response.content


class VideoCapture(SourceCapture):
    """
    Context manager for capturing frames from video url.
    Makes sure that video is opened and closed correctly.
    """

    _cap: cv2.VideoCapture | None = None
    _frames_read: int = 0
    _frames_total: int | None = None
    _fps: float | None = None
    _skip_frames: int | None = None

    def __enter__(self):
        self._cap = cv2.VideoCapture(self.url)
        if self._cap.isOpened():
            self._frames_read = 0
            self._frames_total = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._fps = self._cap.get(cv2.CAP_PROP_FPS)
            self._skip_frames = max(0, int(self._fps / settings.chunk_fps) - 1)
            return self
        else:
            raise ValueError('Can not open video capture')

    def __exit__(self, exc_type, exc_value, traceback):
        self._cap.release()

    def has_next(self) -> bool:
        return self._frames_read < self._frames_total

    async def read(self) -> np.ndarray:
        ret, frame = self._cap.read()
        self._frames_read += 1
        if self._skip_frames:
            self._frames_read += self._skip_frames
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, self._frames_read - 1)
        if ret:
            return frame
        else:
            raise ValueError('Can not read next frame')


class StreamCapture(SourceCapture):
    """
    Context manager for capturing frames from mjpg stream.
    """

    _frame_byte_size: int = 1024

    def has_next(self) -> bool:
        return True

    async def read(self) -> np.ndarray:
        # TODO: Rewrite this mess
        for _ in range(5):
            content_length = None
            bytes = b''
            i = 0
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as resp:
                    async for line in resp.content:
                        i += 1
                        if content_length is not None:
                            if len(bytes) < content_length:
                                bytes += line
                            else:
                                jpg = bytes[2:-2]
                                frame = cv2.imdecode(
                                    np.fromstring(jpg, dtype=np.uint8),
                                    cv2.IMREAD_COLOR
                                )
                                return frame
                        elif b'Content-Length' in line:
                            content_length = int(line.split()[1])
                            if content_length < 100:
                                break
                        elif i > 100:
                            break
        raise ValueError('Can not read next frame')


def open_source(url: str) -> SourceCapture:
    """Get frame capturing context manager for source url"""
    extension = url.lower().split('?')[0].split('.')[-1]
    if extension in STREAM_EXTENSIONS:
        return StreamCapture(url)
    elif extension in VIDEO_EXTENSIONS:
        return VideoCapture(url)
    elif extension in IMAGE_EXTENSIONS:
        return ImageCapture(url)
    else:
        raise ValueError('Unknown source extension')


class VideoWriter:
    def __init__(self, path: Path):
        self.path = path
        self._is_empty = True

    def __enter__(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._out = cv2.VideoWriter(
            filename=self.path.as_posix(),
            fourcc=fourcc,
            fps=settings.chunk_fps,
            frameSize=settings.frame_size,
        )
        if self._out is None or not self._out.isOpened():
            raise ValueError('Can not open video writer')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._out.release()
        if self._is_empty:
            self.path.unlink()

    def write(self, frame: np.ndarray):
        """Write frame into video chunk"""
        self._is_empty = False
        self._out.write(frame)


class ChunkWriter(VideoWriter):
    """
    Context manager for writing frames into video chunk.
    Creates video file and database record.
    Makes sure that video file is opened and closed correctly.
    """

    def __init__(self, source_id: int, path: Path):
        super().__init__(path)
        self.source_id = source_id
        self.start_time = None

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, exc_type, exc_value, traceback):
        raise NotImplementedError

    async def __aenter__(self):
        super().__enter__()
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        end_time = time.time()
        super().__exit__(exc_type, exc_value, traceback)
        if not self._is_empty and exc_type is None:
            chunk = VideoChunkCreate(
                source_id=self.source_id,
                file_path=str(self.path),
                start_time=self.start_time,
                end_time=end_time
            )
            await api_client.create_video_chunk(chunk)


def add_timestamp(frame: np.ndarray, ts: float) -> np.ndarray:
    """
    Add timestamp to frame.

    Parameters:
    - frame (np.ndarray): frame to add timestamp to
    - ts (float): timestamp in seconds

    Returns:
    - frame (np.ndarray): frame with timestamp
    """

    text = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    color = (255, 255, 255)
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = frame.shape[1] - text_size[0] - 10
    text_y = frame.shape[0] - text_size[1] - 10
    cv2.putText(
        frame,
        text,
        (text_x, text_y),
        font,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA
    )
    return frame


class SourceProcessor:
    """Manages background tasks for processing sources."""

    def __init__(self):
        self._tasks = {}

    async def _process(self, source: Source):
        """
        Get frames from the given source and write them into video chunks.
        Create video files and database records.
        Suppoused to be run as a background task.

        Parameters:
        - source (schemas.Source) - source to process
        """
        save_dir = settings.chunks_dir / str(source.id)
        save_dir.mkdir(parents=True, exist_ok=True)
        fps, duration = settings.chunk_fps, settings.chunk_duration
        number_of_frames = int(fps * duration)
        chunks_count = len(list(save_dir.glob('*.mp4')))
        status, status_msg = SourceStatus.FINISHED, ''
        try:
            with open_source(source.url) as cap:
                while cap.has_next():
                    chunk_path = save_dir / f'{chunks_count}.mp4'
                    async with ChunkWriter(source.id, chunk_path) as writer:
                        for _ in range(number_of_frames):
                            if not cap.has_next():
                                break
                            read_time = time.time()
                            frame = await cap.read()
                            frame = cv2.resize(frame, settings.frame_size)
                            if settings.draw_timestamp:
                                frame = add_timestamp(frame, read_time)
                            writer.write(frame)
                            delay = 1 / fps - (time.time() - read_time)
                            if delay > 0:
                                await asyncio.sleep(delay)
                        chunks_count += 1
        except asyncio.CancelledError:
            # Source processing was cancelled by unknown reason,
            # so status should be updated from outside
            self._tasks.pop(source.id)
            return
        except Exception as e:
            status = SourceStatus.ERROR
            status_msg = str(e)
        # Source processing either finished or failed, so status should be
        # updated from inside
        await api_client.update_source_status(source.id, status, status_msg)
        self._tasks.pop(source.id)

    def add(self, source: Source):
        """
        Start processing source.
        If source is already being processed, do nothing.

        Parameters:
        - source (schemas.Source) - source to process
        """
        if source.id not in self._tasks:
            self._tasks[source.id] = asyncio.create_task(self._process(source))

    async def remove(self, source_id: int):
        """
        Stop processing source.

        Parameters:
        - source_id (int) - id of source to stop processing
        """
        if source_id in self._tasks:
            task = self._tasks[source_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def startup(self):
        """Start processing all active sources."""
        sources = await api_client.get_all_active_sources()
        for source in sources:
            self.add(source)

    async def shutdown(self):
        """Stop processing all sources."""
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values())
