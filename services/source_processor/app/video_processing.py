"""
Module for capturing frames from source url and writing them into video chunks

TODO: Clean up code, add comments, refactor
"""

from threading import Thread, Event
from abc import ABC, abstractmethod
from pathlib import Path
import time
from typing import Optional

import requests
import urllib.request
import numpy as np
import cv2

from common.config import settings
from common.constants import SourceStatus
from common.schemas import Source, VideoChunkCreate
from app.clients import api


VIDEO_EXTENSIONS = ['mp4', 'avi', 'mov', 'mkv', 'webm']
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
    def _read(self) -> np.ndarray:
        """Read next frame from source"""
        pass

    def read(self) -> np.ndarray:
        """Safely read next frame from source"""
        for attempt in range(settings.source_processor.capture_max_retries):
            try:
                frame = self._read()
                return frame
            except Exception:
                time.sleep(settings.source_processor.capture_retries_interval)
        raise ValueError('Can not read next frame')


class ImageCapture(SourceCapture):
    """Context manager for capturing frames from image url"""

    def has_next(self) -> bool:
        return True

    def _read(self) -> np.ndarray:
        response = requests.get(self.url)
        if self.url.startswith('http') and response.status != 200:
            raise ValueError('Can not read next frame')
        frame = cv2.imdecode(
            np.frombuffer(response.content, dtype=np.uint8),
            cv2.IMREAD_COLOR
        )
        return frame


class VideoCapture(SourceCapture):
    """
    Context manager for capturing frames from video url.
    Makes sure that video is opened and closed correctly.
    """

    _cap: Optional[cv2.VideoCapture] = None
    _frames_read: int = 0
    _frames_total: Optional[int] = None
    _fps: Optional[float] = None
    _skip_frames: Optional[int] = None

    def __enter__(self):
        self._cap = cv2.VideoCapture(self.url)
        if self._cap.isOpened():
            self._frames_read = 0
            self._frames_total = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._fps = self._cap.get(cv2.CAP_PROP_FPS)
            self._skip_frames = int(self._fps / settings.video.chunk_fps) - 1
            self._skip_frames = max(0, self._skip_frames)
            return self
        else:
            raise ValueError('Can not open video capture')

    def __exit__(self, exc_type, exc_value, traceback):
        self._cap.release()

    def has_next(self) -> bool:
        return self._frames_read < self._frames_total

    def _read(self) -> np.ndarray:
        ret, frame = self._cap.read()
        self._frames_read += 1 + self._skip_frames
        for i in range(self._skip_frames):
            self._cap.read()
        if ret:
            return frame
        raise ValueError('Can not read next frame')


class StreamCapture(SourceCapture):
    """
    Context manager for capturing frames from mjpg stream.
    """

    _frame_byte_size: int = 1024

    def has_next(self) -> bool:
        return True

    def _read(self) -> np.ndarray:
        timeout = settings.source_processor.capture_timeout
        stream = urllib.request.urlopen(self.url, timeout=timeout)
        lines = stream.read(1024).split(b'\r\n')
        content_length = None
        for line in lines:
            if b'Content-Length' in line:
                content_length = int(line.split()[1])
                break
        if content_length is None:
            raise ValueError('Can not read next frame')
        bytes = lines[-1]
        bytes += stream.read(content_length - len(bytes))
        frame = cv2.imdecode(
            np.frombuffer(bytes, dtype=np.uint8),
            cv2.IMREAD_COLOR
        )
        if frame is None:
            raise ValueError('Can not read next frame')
        return frame


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
        self.frame_count: Optional[int] = None
        self._out: Optional[cv2.VideoWriter] = None

    def __enter__(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self._out = cv2.VideoWriter(
            filename=self.path.as_posix(),
            fourcc=fourcc,
            fps=settings.video.chunk_fps,
            frameSize=(
                settings.video.frame_width,
                settings.video.frame_height
            ),
        )
        self.frame_count = 0
        if self._out is None or not self._out.isOpened():
            raise ValueError('Can not open video writer')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._out.release()
        if self.frame_count == 0:
            self.path.unlink()

    def write(self, frame: np.ndarray):
        """Write frame into video chunk"""
        self._out.write(frame)
        self.frame_count += 1


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
        super().__enter__()
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        end_time = time.time()
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is None and self.frame_count > 0:
            db_chunk = VideoChunkCreate(
                source_id=self.source_id,
                file_path=str(self.path),
                start_time=self.start_time,
                end_time=end_time,
                frame_count=self.frame_count,
            )
            # Write chunk to database and publish to RabbitMQ
            db_chunk = api.create_video_chunk(db_chunk)


def task_process_source(source: Source, stop_event: Event,
                        shutdown_event: Event):
    """
    Get frames from the given source and write them into video chunks.
    Create video files and database records.
    Suppoused to be run as a background task in a separate thread.

    Parameters:
    - source (schemas.Source) - source to process
    - stop_event (threading.Event) - event to stop processing
    - shutdown_event (threading.Event) - event which is set when source
        processor is shutting down, no source status updates are needed
        in this case
    """
    save_dir = settings.paths.chunks_dir / str(source.id)
    save_dir.mkdir(parents=True, exist_ok=True)
    fps, duration = settings.video.chunk_fps, settings.video.chunk_duration
    frame_size = (settings.video.frame_width, settings.video.frame_height)
    number_of_frames = int(fps * duration)
    chunks_count = len(list(save_dir.glob('*.mp4')))
    status, status_msg = SourceStatus.FINISHED, 'Reached the end'
    try:
        with open_source(source.url) as cap:
            while cap.has_next():
                chunk_path = save_dir / f'{chunks_count}.mp4'
                with ChunkWriter(source.id, chunk_path) as writer:
                    for _ in range(number_of_frames):
                        if not cap.has_next() or stop_event.is_set():
                            break
                        start_time = time.perf_counter()
                        end_time = start_time + 1 / fps
                        frame = cap.read()
                        frame = cv2.resize(frame, frame_size)
                        writer.write(frame)
                        delay = end_time - time.perf_counter()
                        if delay > 0:
                            time.sleep(delay)
                        else:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning('Frame processing took too long')
                    chunks_count += 1
                if stop_event.is_set():
                    status, status_msg = SourceStatus.PAUSED, 'Stopped by user'
                    break
    except Exception as e:
        status = SourceStatus.ERROR
        status_msg = str(e)
    # Source processing either finished or failed, so status should be
    # updated from inside
    if not shutdown_event.is_set():
        api.update_source_status(source.id, status, status_msg)


class SourceProcessor:
    """Manages background tasks for processing sources."""

    def __init__(self):
        self._threads = {}
        self._stop_events = {}
        self._shutdown_event = Event()

    def clean_finished(self):
        """Remove threads of finished sources"""
        for source_id, thread in self._threads.copy().items():
            if not thread.is_alive():
                self._threads[source_id].join()
                del self._threads[source_id]
                del self._stop_events[source_id]

    def add(self, source: Source):
        """
        Start processing source.
        If source is already being processed, do nothing.

        Parameters:
        - source (schemas.Source) - source to process
        """
        self.clean_finished()
        if source.id not in self._threads:
            stop_event = Event()
            thread = Thread(
                target=task_process_source,
                args=(source, stop_event, self._shutdown_event,),
                daemon=True,
            )
            thread.start()
            self._threads[source.id] = thread
            self._stop_events[source.id] = stop_event

    def remove(self, source_id: int):
        """
        Stop processing source.
        If source is not being processed, do nothing.

        Parameters:
        - source_id (int) - id of source to stop processing
        """
        self.clean_finished()
        if source_id in self._threads:
            self._stop_events[source_id].set()

    def startup(self):
        """Start processing all active sources."""
        self._shutdown_event.clear()
        sources = api.get_all_sources(SourceStatus.ACTIVE)
        for source in sources:
            self.add(source)

    def shutdown(self):
        """Stop processing all sources."""
        self._shutdown_event.set()
        for source_id in list(self._threads.keys()):
            self.remove(source_id)
        while self._threads:
            self.clean_finished()
            time.sleep(0.1)
