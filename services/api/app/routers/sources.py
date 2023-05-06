import os
from pathlib import Path
import re
import shutil

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app import crud, schemas
from app.models import SourceStatus
from app.dependencies import SourceProcessorDep
from app.security import RequiresAuthDep


router = APIRouter(
    prefix="/sources",
    tags=["Source management"]
)


@router.post(
    "/create/url",
    response_model=schemas.Source,
    summary="Create source from url",
    response_description="Source created"
)
async def create_from_url(name: str, url: str, auth: RequiresAuthDep):
    """
    Create source from url.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **url**: url of the source, must be accessible. Supported extensions:
        - video: mp4, avi
        - video stream: mjpg
        - image: png, jpg, jpeg
    """
    user, session = auth
    sources = await crud.sources.read_non_finished(
        session=session,
        user_id=user.id if not user.is_admin else None
    )
    if user.max_sources >= 0 and len(sources) >= user.max_sources:
        raise HTTPException(status_code=400, detail="Source limit exceeded")
    source = await crud.sources.create(session, name, url, user.id)
    return source


@router.post(
    "/create/file",
    response_model=schemas.Source,
    summary="Create source from file",
    response_description="Source created"
)
async def create_from_file(name: str, file: UploadFile,
                           auth: RequiresAuthDep):
    """
    Create source from file.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **file**: video file. Supported extensions: mp4, avi
    """
    user, session = auth
    sources = await crud.sources.read_non_finished(
        session=session,
        user_id=user.id if not user.is_admin else None
    )
    if user.max_sources >= 0 and len(sources) >= user.max_sources:
        raise HTTPException(status_code=400, detail="Source limit exceeded")
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
    source = await crud.sources.create(session, name, path.as_uri(), user.id)
    return source


@router.get(
    "/get/{id:int}",
    response_model=schemas.Source,
    summary="Get source by id",
    response_description="Source found"
)
async def get(id: int,  auth: RequiresAuthDep):
    """
    Get source by id.

    Parameters:
    - **id**: source id
    """
    user, session = auth
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user.id if not user.is_admin else None
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get(
    "/get/all",
    response_model=list[schemas.Source],
    summary="Get list of all sources",
    response_description="List of all sources"
)
async def get_all(auth: RequiresAuthDep):
    """
    Get list of all sources.
    """
    user, session = auth
    sources = await crud.sources.read_all(
        session=session,
        user_id=user.id if not user.is_admin else None
    )
    return sources


@router.get(
    "/get/non-finished",
    response_model=list[schemas.Source],
    summary="Get list of non-finished sources",
    response_description="List of non-finished sources"
)
async def get_non_finished(auth: RequiresAuthDep):
    """
    Get list of non-finished sources.
    """
    user, session = auth
    sources = await crud.sources.read_non_finished(
        session=session,
        user_id=user.id if not user.is_admin else None
    )
    return sources


@router.put(
    "/start",
    summary="Start source"
)
async def start(id: int, auth: RequiresAuthDep,
                source_processor: SourceProcessorDep):
    """
    Start source processing in background:
    - Get frames from source url
    - Save frames to disk as video chunks
    - Create database records for video chunks
    - Send video chunks to RabbitMQ queue

    Parameters:
    - **id**: source id
    """
    user, session = auth
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user.id if not user.is_admin else None
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source already active")
    await crud.sources.update_status(session, id, SourceStatus.ACTIVE)
    source_processor.add(source)


@router.put(
    "/pause",
    summary="Pause source"
)
async def pause(id: int, auth: RequiresAuthDep,
                source_processor: SourceProcessorDep):
    """
    Pause source processing.

    Parameters:
    - **id**: source id
    """
    user, session = auth
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user.id if not user.is_admin else None
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code != SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source not active")
    if source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    await source_processor.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.PAUSED)


@router.put(
    "/finish",
    summary="Finish source"
)
async def finish(id: int, auth: RequiresAuthDep,
                 source_processor: SourceProcessorDep):
    """
    Finish source processing. Finished source can't be started again.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Parameters:
    - **id**: source id
    """
    user, session = auth
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user.id if not user.is_admin else None
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    if source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.FINISHED)


@router.delete(
    "/delete",
    summary="Delete source"
)
async def delete(id: int, auth: RequiresAuthDep,
                 source_processor: SourceProcessorDep):
    """
    Remove source.
    Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.
    """
    user, session = auth
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user.id if not user.is_admin else None
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.sources.delete(session, id)  # Chunks are deleted by cascade
    if source.url.startswith('file://'):  # Delete source file if local
        path = Path(source.url[7:])
        path.unlink()
    shutil.rmtree(settings.chunks_dir / str(id))  # Delete video chunks
