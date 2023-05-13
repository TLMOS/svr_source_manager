from fastapi import APIRouter, HTTPException

from common import schemas
from app import crud
from app.dependencies import SessionDep


router = APIRouter(
    prefix="/videos",
    tags=["Video managment"]
)


@router.post(
    "/chunks/create",
    response_model=schemas.VideoChunk,
    summary="Create chunk record",
    response_description="Chunk created"
)
async def create_chunk(session: SessionDep,
                       chunk: schemas.VideoChunkCreate):
    """
    Create video chunk record.

    Parameters:
    - **chunk**: video chunk create schema.
    """
    db_source = await crud.sources.read(session, chunk.source_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return await crud.video_chunks.create(session, chunk)
