from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
import cv2

from app import crud
from app.config import settings
from app.database import SessionDep
from app.utils import open_video_capture, open_video_writer, TmpFilePath
from app.security import ExposedDep


router = APIRouter(
    prefix="/api",
    tags=["Exposed API"],
    dependencies=[ExposedDep]
)


@router.get(
    "/get/frame/timestamp",
    summary="Get frame by timestamp",
    response_description="Frame",
    response_class=Response
)
async def get_frame_by_timestamp(session: SessionDep, source_id: int,
                                 timestamp: float):
    """
    Get frame by timestamp.

    Parameters:
    - source_id (int): source id
    - timestamp (float): timestamp in seconds

    Raises:
    - HTTPException 400: If frame capture failed
    - HTTPException 404: If no corresponding video chunk found in
        the database

    Returns:
    - Response: frame
    """
    chunk = await crud.video_chunks.read_by_timestamp(session, source_id,
                                                      timestamp)
    if chunk is None:
        raise HTTPException(status_code=404,
                            detail="No frame saved at this timestamp")
    with open_video_capture(chunk.file_path) as cap:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp - chunk.start_time)
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400, detail="Frame capture failed")
        _, buffer = cv2.imencode(".jpg", frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get(
    "/get/video/chunk",
    summary="Get video chunk",
    response_description="Video chunk",
    response_class=FileResponse
)
async def get_video_chunk(session: SessionDep, chunk_id: int):
    """
    Get video chunk.

    Parameters:
    - chunk_id (int): video chunk id

    Raises:
    - HTTPException 404: If no corresponding video chunk found in
        the database

    Returns:
    - FileResponse: video chunk
    """
    chunk = await crud.video_chunks.read(session, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Video chunk not found")
    return FileResponse(path=chunk.file_path, media_type="video/mp4")


@router.get(
    "/get/video/part",
    summary="Get video part in given time interval",
    response_description="Video part",
    response_class=FileResponse
)
async def get_video_part(session: SessionDep, source_id: int,
                         start_time: float, end_time: float):
    """
    Get video part in given time interval.

    Parameters:
    - source_id (int): source id
    - start_time (float): start time in seconds
    - end_time (float): end time in seconds

    Raises:
    - HTTPException 404: If no corresponding video chunk found in
        the database

    Returns:
    - FileResponse: video part
    """
    chunks = await crud.video_chunks.read_all_in_interval(
            session, source_id, start_time, end_time
    )
    if not chunks:
        raise HTTPException(
                status_code=404,
                detail="No video chunks found in given interval"
        )
    with TmpFilePath('.mp4') as path:
        with open_video_writer(path) as out:
            for i, chunk in enumerate(chunks):
                uri = Path(chunk.file_path).as_uri()
                with open_video_capture(uri) as cap:
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    if i == 0 and start_time > chunk.start_time:
                        cap.set(cv2.CAP_PROP_POS_MSEC,
                                start_time - chunk.start_time)
                    if i == len(chunks) - 1 and end_time < chunk.end_time:
                        frame_count = (end_time - chunk.start_time) \
                                            / settings.video_fps
                    for _ in range(frame_count):
                        ret, frame = cap.read()
                        if ret:
                            out.write(frame)
        return FileResponse(path=path, media_type="video/mp4")
