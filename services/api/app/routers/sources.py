import os
from pathlib import Path
import re
import shutil

from fastapi import APIRouter, HTTPException, UploadFile

from common.constants import SourceStatus
from common import schemas
from app.config import settings
from app import crud
from app.dependencies import SessionDep
from app.clients import source_processor


router = APIRouter(
    prefix='/sources',
    tags=['Source management']
)


@router.post(
    '/create/url',
    response_model=schemas.Source,
    summary='Create source from url',
    response_description='Source created'
)
async def create_from_url(session: SessionDep, name: str, url: str):
    """
    Create source from url.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - name (str): name of the source, allows duplicates
    - url (str): video url

    Returns:
    - schemas.Source: created source
    """
    source = schemas.SourceCreate(name=name, url=url)
    return await crud.sources.create(session, source)


@router.post(
    '/create/file',
    response_model=schemas.Source,
    summary='Create source from file',
    response_description='Source created'
)
async def create_from_file(session: SessionDep, name: str, file: UploadFile):
    """
    Create source from file.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - name (str): name of the source, allows duplicates
    - file (UploadFile): video file

    Returns:
    - schemas.Source: created source
    """
    file_name = file.filename.replace(' ', '_')
    file_name = re.sub(r'[^a-zA-Z0-9_.-]', '', file_name)
    path = settings.sources_dir / file_name
    count = 1
    while path.is_file():
        stem, ext = os.path.splitext(file_name)
        path = settings.sources_dir / f'{stem}_{count}{ext}'
        count += 1
    with open(path, 'wb') as out_file:
        while content := file.file.read(1024):
            out_file.write(content)
    source = schemas.SourceCreate(name=name, url=path.as_uri())
    return await crud.sources.create(session, source)


@router.get(
    '/get/{id:int}',
    response_model=schemas.Source,
    summary='Get source by id',
    response_description='Source found'
)
async def get(session: SessionDep, id: int):
    """
    Get source by id.

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database

    Returns:
    - schemas.Source: source
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    return db_source


@router.get(
    '/get/all',
    response_model=list[schemas.Source],
    summary='Get list of all sources',
    response_description='List of all sources'
)
async def get_all(session: SessionDep, status: SourceStatus | None = None):
    """
    Get list of all sources.

    Parameters:
    - status (SourceStatus): filter by status

    Returns:
    - list[schemas.Source]: list of all sources
    """
    db_sources = await crud.sources.read_all(session, status)
    return db_sources


@router.get(
    '/get/time_coverage',
    summary='Get all saved time intervals from source',
    response_description='Video chunks',
    response_model=list[tuple[float, float]]
)
async def get_time_coverage(session: SessionDep, id: int):
    """
    Get all saved time intervals from source.

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database

    Returns:
    - list[tuple[float, float]]: list of time intervals (start, end)
    """
    db_chunks = await crud.video_chunks.read_all(session, id)
    if db_chunks is None:
        raise HTTPException(status_code=404, detail='Video chunks not found')
    return [(db_chunk.start_time, db_chunk.end_time) for db_chunk in db_chunks]


@router.put(
    '/start',
    summary='Start source'
)
async def start(session: SessionDep, id: int):
    """
    Start source processing in background:
    - Get frames from source url
    - Save frames to disk as video chunks
    - Create database records for video chunks
    - Send video chunks to RabbitMQ queue

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database
    - HTTPException 400: If source already active
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    if db_source.status_code == SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail='Source already active')
    await crud.sources.update_status(session, id, SourceStatus.ACTIVE)
    await source_processor.add(db_source)


@router.put(
    '/pause',
    summary='Pause source'
)
async def pause(session: SessionDep, id: int):
    """
    Pause source processing.

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database
    - HTTPException 400: If source not active
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    if db_source.status_code != SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail='Source not active')
    await source_processor.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.PAUSED)


@router.put(
    '/finish',
    summary='Finish source'
)
async def finish(session: SessionDep, id: int):
    """
    Pause source processing and mark it as finished.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database
    - HTTPException 400: If source already finished
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    if db_source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail='Source already finished')
    if db_source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.FINISHED)


@router.put(
    '/update_status',
    summary='Update source status'
)
async def update_status(session: SessionDep, id: int, status: SourceStatus,
                        status_msg: str = None):
    """
    Update source status and status message.

    Parameters:
    - id (int): source id
    - status (SourceStatus): new status
    - status_msg (str): new status message

    Raises:
    - HTTPException 404: If source not found in the database
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    await crud.sources.update_status(session, id, status, status_msg)


@router.delete(
    '/delete',
    summary='Delete source'
)
async def delete(session: SessionDep, id: int):
    """
    Remove source.
    Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.

    Parameters:
    - id (int): source id

    Raises:
    - HTTPException 404: If source not found in the database
    """
    db_source = await crud.sources.read(session, id)
    if db_source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    if db_source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.sources.delete(session, id)  # Chunks are deleted by cascade
    if db_source.url.startswith('file://'):  # Delete source file if local
        path = Path(db_source.url[7:])
        path.unlink()
    source_dir = settings.chunks_dir / str(id)
    if source_dir.is_dir():
        shutil.rmtree(source_dir)  # Delete video chunks
