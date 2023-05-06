from app.api_client.base import Router


route = Router('videos')


def get_time_coverage(source_id: int) -> list[tuple[float, float]]:
    """
    Get all saved time intervals from source.

    Args:
        source_id: Source id.
    """
    return route.request('GET', 'get/time_coverage',
                         source_id=source_id).json()


def get_frame(source_id: int, timestamp: float) -> bytes:
    """
    Get frame from source by timestamp.

    Args:
        source_id: Source id.
        timestamp: Timestamp of frame in seconds.
    """
    return route.request('GET', 'get/frame', source_id=source_id,
                         timestamp=timestamp).content


def get_last_frame(source_id: int) -> bytes:
    """
    Get last frame from source.

    Args:
        source_id: Source id.
    """
    return route.request('GET', 'get/frame/last',
                         source_id=source_id).content


def get_video_segment(source_id: int, start: float, end: float) -> bytes:
    """
    Get video segment from source by time interval.
    Resulting video may contain gaps, if source was paused during processing.

    Args:
        source_id: Source id.
        start: Start time of video segment in seconds.
        end: End time of video segment in seconds.
    """
    return route.request('GET', 'get/segment', source_id=source_id,
                         start_time=start, end_time=end).content
