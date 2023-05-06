from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, FileResponse
import cv2

from app.config import settings
from app import crud
from app.dependencies import TmpFilePath
from app.video_processing import VideoCapture, VideoWriter
from app.security import RequiresAuthDep


router = APIRouter(
    prefix="/videos",
    tags=["Retrieve video data"],
)


@router.get(
    "/get/time_coverage",
    summary="Get all saved time intervals from source",
    response_description="Video chunks",
    response_model=list[tuple[float, float]]
)
async def get_time_coverage(source_id: int, auth: RequiresAuthDep):
    """
    Get all saved time intervals from source.

    Parameters:
    - **source_id**: source id
    """
    user, session = auth
    chunks = await crud.video_chunks.read_all(
        session=session,
        source_id=source_id,
        user_id=user.id if not user.is_admin else None
    )
    if chunks is None:
        raise HTTPException(status_code=404, detail="Video chunks not found")
    return [(chunk.start_time, chunk.end_time) for chunk in chunks]


@router.get(
    "/get/frame",
    summary="Get frame by timestamp",
    response_description="Frame",
    response_class=Response
)
async def get_frame(source_id: int, timestamp: float, auth: RequiresAuthDep):
    """
    Get frame from source by timestamp.

    Parameters:
    - **source_id**: source id
    - **timestamp**: timestamp in seconds
    """
    user, session = auth
    chunk = await crud.video_chunks.read_by_timestamp(
        session=session,
        source_id=source_id,
        timestamp=timestamp,
        user_id=user.id if not user.is_admin else None
    )
    if chunk is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    with VideoCapture(chunk.file_path) as cap:
        frame_number = int((timestamp - chunk.start_time) * settings.chunk_fps)
        cap.skip(frame_number)
        frame = cap.read()
        _, buffer = cv2.imencode('.jpg', frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get(
    "/get/frame/last",
    summary="Get last frame",
    response_description="Frame",
    response_class=Response
)
async def get_last_frame(source_id: int, auth: RequiresAuthDep):
    """
    Get last frame from source.

    Parameters:
    - **source_id**: source id
    """
    user, session = auth
    chunk = await crud.video_chunks.read_last(
        session=session,
        source_id=source_id,
        user_id=user.id if not user.is_admin else None
    )
    if chunk is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    with VideoCapture(chunk.file_path) as cap:
        cap.skip(cap.frames_total - 1)
        frame = cap.read()
        _, buffer = cv2.imencode('.jpg', frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get(
    "/get/segment",
    summary="Get video segment by time interval",
    response_description="Video segment",
    response_class=FileResponse
)
async def get_video_segment(source_id: int, start_time: float, end_time: float,
                            auth: RequiresAuthDep,
                            tmp_path: Path = Depends(TmpFilePath('.mp4'))):
    """
    Get video segment from source by time interval.
    Resulting video may contain gaps, if source was paused during processing.

    Parameters:
    - **source_id**: source id
    - **start_time**: start timestamp in seconds
    - **end_time**: end timestamp in seconds
    """
    user, session = auth
    chunks = await crud.video_chunks.read_all_in_interval(
        session=session,
        source_id=source_id,
        start_time=start_time,
        end_time=end_time,
        user_id=user.id if not user.is_admin else None
    )
    if not chunks:
        raise HTTPException(status_code=404, detail="Video segment not found")
    with VideoWriter(tmp_path) as out:
        for i, chunk in enumerate(chunks):
            uri = Path(chunk.file_path).as_uri()
            with VideoCapture(uri) as cap:
                if i == 0 and start_time > chunk.start_time:
                    # Skip frames before start_time
                    cap.skip(int(
                        (start_time - chunk.start_time) * settings.chunk_fps
                    ))
                if i == len(chunks) - 1 and end_time < chunk.end_time:
                    # Skip frames after end_time
                    cap.frames_total = \
                        int((end_time - chunk.start_time) * settings.chunk_fps)
                while cap.has_next():
                    frame = cap.read()
                    out.write(frame)
    return FileResponse(
        path=tmp_path,
        filename=f'{source_id}_{start_time}_{end_time}.mp4',
        media_type="video/mp4"
    )
