import asyncio
import tempfile
from pathlib import Path

import cv2
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import Response, FileResponse

from common import schemas
from common.config import settings
from common.utils.videos import open_video_capture, open_video_writer
from common.database import crud
from app.clients.rabbitmq import publish_video_chunk
from app.security import auth
from app.dependencies import DatabaseDepends


router = APIRouter(
    prefix='/videos',
    tags=['Video managment'],
    dependencies=[Security(auth.requires_auth)]
)


@router.post(
    '/chunks/create',
    response_model=schemas.VideoChunk,
    summary='Create chunk record',
    response_description='Chunk created'
)
async def create_chunk(db: DatabaseDepends,
                       chunk: schemas.VideoChunkCreate):
    """
    Create video chunk record and publish to RabbitMQ.

    Parameters:
    - chunk: video chunk create schema.

    Raises:
    - HTTPException 404: If source not found in the database

    Returns:
    - schemas.VideoChunk: created video chunk
    """
    db_source = await crud.sources.read(db, chunk.source_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    db_chunk = await crud.video_chunks.create(db, chunk)
    asyncio.create_task(publish_video_chunk(db_chunk))
    return db_chunk


@router.get(
    '/get/frame/{chunk_id}/{frame_id}',
    summary='Get frame by id',
    response_description='Frame',
    response_class=Response
)
async def get_frame_by_id(db: DatabaseDepends, chunk_id: int, frame_id: int):
    """
    Get frame by id.

    Parameters:
    - chunk_id (int): video chunk id
    - frame_id (int): frame id (number of frame in video chunk)
    """
    db_chunk = await crud.video_chunks.read(db, chunk_id)
    if db_chunk is None:
        raise HTTPException(status_code=404, detail='Video chunk not found')
    with open_video_capture(db_chunk.file_path) as cap:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400, detail='Frame capture failed')
        _, buffer = cv2.imencode('.png', frame)
        return Response(content=buffer.tobytes(),
                        media_type='image/png')


@router.get(
    '/get/frame/last',
    summary='Get last saved frame from source',
    response_description='Frame',
    response_class=Response
)
async def get_last_frame(db: DatabaseDepends, source_id: int):
    """
    Get last frame from source.

    Parameters:
    - source_id: source id

    Raises:
    - HTTPException 400: If frame capture failed
    - HTTPException 404: If no corresponding video chunk found in
                         the database
    """
    db_chunk = await crud.video_chunks.read_last(db, source_id)
    if db_chunk is None:
        raise HTTPException(status_code=404, detail='Frame not found')
    with open_video_capture(db_chunk.file_path) as cap:
        cap_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, cap_length - 1)
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400,
                                detail='Frame capture failed')
        _, buffer = cv2.imencode('.png', frame)
        return Response(content=buffer.tobytes(),
                        media_type='image/png')


@router.get(
    '/get/frame/timestamp',
    summary='Get frame by timestamp',
    response_description='Frame',
    response_class=Response
)
async def get_frame_by_timestamp(db: DatabaseDepends, source_id: int,
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
    chunk = await crud.video_chunks.read_by_timestamp(db, source_id,
                                                      timestamp)
    if chunk is None:
        raise HTTPException(status_code=404,
                            detail='No frame saved at this timestamp')
    duration = chunk.end_time - chunk.start_time
    frame = chunk.frame_count * (timestamp - chunk.start_time) / duration
    with open_video_capture(chunk.file_path) as cap:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame))
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400, detail='Frame capture failed')
        _, buffer = cv2.imencode('.png', frame)
        return Response(content=buffer.tobytes(), media_type='image/png')


@router.get(
    '/get/chunk',
    summary='Get video chunk',
    response_description='Video chunk',
    response_class=FileResponse
)
async def get_video_chunk(db: DatabaseDepends, chunk_id: int):
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
    chunk = await crud.video_chunks.read(db, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail='Video chunk not found')
    return FileResponse(path=chunk.file_path, media_type='video/mp4')


@router.get(
    '/get/part',
    summary='Get video part in given time interval',
    response_description='Video part',
    response_class=FileResponse
)
async def get_video_part(db: DatabaseDepends, source_id: int,
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
            db, source_id, start_time, end_time
    )
    if not chunks:
        raise HTTPException(
                status_code=404,
                detail='No video chunks found in given interval'
        )
    with tempfile.NamedTemporaryFile(dir=settings.paths.tmp_dir) as f:
        with open_video_writer(f.name) as out:
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
        return FileResponse(path=f.name, media_type='video/mp4')
