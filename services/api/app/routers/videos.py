from fastapi import APIRouter, HTTPException

from app import crud, schemas
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
                       chunk_schema: schemas.VideoChunkCreate):
    """
    Create video chunk record.

    Parameters:
    - **chunk**: video chunk create schema.
    """
    source = await crud.sources.read(session, chunk_schema.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    chunk = await crud.video_chunks.create(session, chunk_schema)
    return chunk
