from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import cv2

from common import schemas
from app import crud
from app.dependencies import SessionDep
from app.utils import open_video_capture


router = APIRouter(
    prefix='/videos',
    tags=['Video managment']
)


@router.post(
    '/chunks/create',
    response_model=schemas.VideoChunk,
    summary='Create chunk record',
    response_description='Chunk created'
)
async def create_chunk(session: SessionDep,
                       chunk: schemas.VideoChunkCreate):
    """
    Create video chunk record.

    Parameters:
    - chunk: video chunk create schema.

    Raises:
    - HTTPException 404: If source not found in the database

    Returns:
    - schemas.VideoChunk: created video chunk
    """
    db_source = await crud.sources.read(session, chunk.source_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    return await crud.video_chunks.create(session, chunk)


@router.get(
    '/frames/get/last',
    summary='Get last saved frame from source',
    response_description='Frame',
    response_class=Response
)
async def get_last_frame(session: SessionDep, source_id: int):
    """
    Get last frame from source.

    Parameters:
    - source_id: source id

    Raises:
    - HTTPException 400: If frame capture failed
    - HTTPException 404: If no corresponding video chunk found in
        the database
    """
    db_chunk = await crud.video_chunks.read_last(session, source_id)
    if db_chunk is None:
        raise HTTPException(status_code=404, detail='Frame not found')
    with open_video_capture(db_chunk.file_path) as cap:
        cap_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, cap_length - 1)
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400,
                                detail='Frame capture failed')
        _, buffer = cv2.imencode('.jpg', frame)
        return Response(content=buffer.tobytes(),
                        media_type='image/jpeg')
