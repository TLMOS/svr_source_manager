import os
from pathlib import Path
import re
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, Response

from common.constants import SourceStatus, UserRole
from common import schemas
from app.config import settings
from app import crud, source_processor_client
from app.dependencies import SessionDep, UserIdDep, UserRoleDep


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
async def create_from_url(session: SessionDep,
                          user_id: UserIdDep,
                          name: str,
                          url: str):
    """
    Create source from url.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **url**: url of the source, must be accessible. Supported extensions:
        - video: mp4, avi
        - video stream: mjpg
    """
    db_user = await crud.users.read(session, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_sources = await crud.sources.read_non_finished(session, user_id)
    if db_user.max_sources >= 0 and len(db_sources) >= db_user.max_sources:
        raise HTTPException(status_code=400, detail="Source limit exceeded")
    return await crud.sources.create(session, name, url, db_user.id)


@router.post(
    "/create/file",
    response_model=schemas.Source,
    summary="Create source from file",
    response_description="Source created"
)
async def create_from_file(session: SessionDep,
                           user_id: UserIdDep,
                           name: str,
                           file: UploadFile):
    """
    Create source from file.
    By default, the source is paused. To start it, use the /sources/start

    Parameters:
    - **name**: name of the source, allows duplicates
    - **file**: video file. Supported extensions: mp4, avi
    """
    db_user = await crud.users.read(session, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    sources = await crud.sources.read_non_finished(session, user_id)
    if db_user.max_sources >= 0 and len(sources) >= db_user.max_sources:
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

    return await crud.sources.create(session, name, path.as_uri(), db_user.id)


@router.get(
    "/get/{id:int}",
    response_model=schemas.Source,
    summary="Get source by id",
    response_description="Source found"
)
async def get(session: SessionDep,
              user_id: UserIdDep,
              user_role: UserRoleDep,
              id: int):
    """
    Get source by id.

    Parameters:
    - **id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return db_source


@router.get(
    "/get/all",
    response_model=list[schemas.Source],
    summary="Get list of all sources",
    response_description="List of all sources"
)
async def get_all(session: SessionDep,
                  user_id: UserIdDep,
                  user_role: UserRoleDep,
                  status: SourceStatus | None = None):
    """
    Get list of all sources.

    Params:
    Parameters:
    - **status**: (optional) If specified, will return only sources with
                  given status
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_sources = await crud.sources.read_all(session, status, user_id)
    return db_sources


@router.get(
    "/get/non-finished",
    response_model=list[schemas.Source],
    summary="Get list of non-finished sources",
    response_description="List of non-finished sources"
)
async def get_non_finished(session: SessionDep,
                           user_id: UserIdDep,
                           user_role: UserRoleDep):
    """
    Get list of non-finished sources.
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    return await crud.sources.read_non_finished(session, user_id)


@router.get(
    "/get/frame",
    summary="Get frame",
    response_description="Frame",
    response_class=Response
)
async def get_frame(session: SessionDep,
                    user_id: UserIdDep,
                    user_role: UserRoleDep,
                    id: int):
    """
    Get frame from source.

    Parameters:
    - **source_id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user_id
    )
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    frame = source_processor_client.get_frame(id)
    return Response(content=frame, media_type="image/jpeg")


@router.get(
    "/get/time_coverage",
    summary="Get all saved time intervals from source",
    response_description="Video chunks",
    response_model=list[tuple[float, float]]
)
async def get_time_coverage(session: SessionDep,
                            user_id: UserIdDep,
                            user_role: UserRoleDep,
                            id: int):
    """
    Get all saved time intervals from source.

    Parameters:
    - **source_id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_chunks = await crud.video_chunks.read_all(session, id, user_id)
    if db_chunks is None:
        raise HTTPException(status_code=404, detail="Video chunks not found")
    return [(db_chunk.start_time, db_chunk.end_time) for db_chunk in db_chunks]


@router.put(
    "/start",
    summary="Start source"
)
async def start(session: SessionDep,
                user_id: UserIdDep,
                user_role: UserRoleDep,
                id: int):
    """
    Start source processing in background:
    - Get frames from source url
    - Save frames to disk as video chunks
    - Create database records for video chunks
    - Send video chunks to RabbitMQ queue

    Parameters:
    - **id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if db_source.status_code == SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source already active")
    await crud.sources.update_status(session, id, SourceStatus.ACTIVE)
    source_processor_client.add(db_source)


@router.put(
    "/pause",
    summary="Pause source"
)
async def pause(session: SessionDep,
                user_id: UserIdDep,
                user_role: UserRoleDep,
                id: int):
    """
    Pause source processing.

    Parameters:
    - **id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if db_source.status_code != SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source not active")
    if db_source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    source_processor_client.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.PAUSED)


@router.put(
    "/finish",
    summary="Finish source"
)
async def finish(session: SessionDep,
                 user_id: UserIdDep,
                 user_role: UserRoleDep,
                 id: int):
    """
    Finish source processing. Finished source can't be started again.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Parameters:
    - **id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if db_source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    if db_source.status_code == SourceStatus.ACTIVE:
        source_processor_client.remove(id)
    await crud.sources.update_status(session, id, SourceStatus.FINISHED)


@router.put(
    "/update_status",
    summary="Update source status"
)
async def update_status(session: SessionDep,
                        user_id: UserIdDep,
                        user_role: UserRoleDep,
                        id: int,
                        status: SourceStatus,
                        status_msg: str = None):
    """
    Update source status and status message.

    Parameters:
    - **id**: source id
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    await crud.sources.update_status(session, id, status, status_msg)


@router.delete(
    "/delete",
    summary="Delete source"
)
async def delete(session: SessionDep,
                 user_id: UserIdDep,
                 user_role: UserRoleDep,
                 id: int):
    """
    Remove source.
    Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.
    """
    user_id = None if user_role == UserRole.ADMIN else user_id
    db_source = await crud.sources.read(session, id, user_id)
    if db_source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if db_source.status_code == SourceStatus.ACTIVE:
        source_processor_client.remove(id)
    await crud.sources.delete(session, id)  # Chunks are deleted by cascade
    if db_source.url.startswith('file://'):  # Delete source file if local
        path = Path(db_source.url[7:])
        path.unlink()
    source_dir = settings.chunks_dir / str(id)
    if source_dir.is_dir():
        shutil.rmtree(source_dir)  # Delete video chunks
