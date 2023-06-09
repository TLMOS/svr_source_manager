from pathlib import Path
from contextlib import contextmanager

import cv2

from common.config import settings


@contextmanager
def open_video_capture(path: str | Path) -> cv2.VideoCapture:
    """
    Context manager to open a video capture and release it after use.

    Parameters:
    - path (Path): path to the video file

    Returns:
    - cv2.VideoCapture: video capture

    Usage:
        ```python
        with open_video_capture(path) as cap:
            # do something with cap
        ```
    """
    try:
        cap = cv2.VideoCapture(str(path))
        yield cap
    finally:
        cap.release()


@contextmanager
def open_video_writer(path: str | Path) -> cv2.VideoWriter:
    """
    Context manager to open a video writer and safely release it after use.
    Uses default video settings, same as used in the source processor.

    Parameters:
    - path (Path): path to the video file

    Returns:
    - cv2.VideoWriter: video writer

    Usage:
        ```python
        with open_video_writer(path) as out:
            # do something with out
        ```
    """
    if type(path) == str:
        path = Path(path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    try:
        out = cv2.VideoWriter(
            filename=path.as_posix(),
            fourcc=fourcc,
            fps=settings.video.chunk_fps,
            frameSize=(
                settings.video.frame_width,
                settings.video.frame_height
            ),
        )
        yield out
    finally:
        out.release()
