import os
from pathlib import Path
import re
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, Response
import cv2

from app.config import settings
from app import crud, schemas
from app.models import SourceStatus
from app.dependencies import SourceProcessorDep, SessionDep, UserIdDep


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
        - image: png, jpg, jpeg
    """
    user = await crud.users.read(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    sources = await crud.sources.read_non_finished(session, user_id)
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
    user = await crud.users.read(session, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    sources = await crud.sources.read_non_finished(session, user_id)
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
async def get(session: SessionDep,
              user_id: UserIdDep,
              id: int):
    """
    Get source by id.

    Parameters:
    - **id**: source id
    """
    source = await crud.sources.read(session, id, user_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.get(
    "/get/all",
    response_model=list[schemas.Source],
    summary="Get list of all sources",
    response_description="List of all sources"
)
async def get_all(session: SessionDep,
                  user_id: UserIdDep):
    """
    Get list of all sources.
    """
    sources = await crud.sources.read_all(session, user_id)
    return sources


@router.get(
    "/get/non-finished",
    response_model=list[schemas.Source],
    summary="Get list of non-finished sources",
    response_description="List of non-finished sources"
)
async def get_non_finished(session: SessionDep,
                           user_id: UserIdDep):
    """
    Get list of non-finished sources.
    """
    sources = await crud.sources.read_non_finished(session, user_id)
    return sources


@router.get(
    "/get/frame",
    summary="Get frame",
    response_description="Frame",
    response_class=Response
)
async def get_frame(session: SessionDep,
                    source_processor: SourceProcessorDep,
                    user_id: UserIdDep,
                    id: int):
    """
    Get frame from source.

    Parameters:
    - **source_id**: source id
    """
    source = await crud.sources.read(
        session=session,
        id=id,
        user_id=user_id
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    frame = await source_processor.get_frame(id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    _, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")


@router.get(
    "/get/time_coverage",
    summary="Get all saved time intervals from source",
    response_description="Video chunks",
    response_model=list[tuple[float, float]]
)
async def get_time_coverage(session: SessionDep,
                            user_id: UserIdDep,
                            id: int):
    """
    Get all saved time intervals from source.

    Parameters:
    - **source_id**: source id
    """
    chunks = await crud.video_chunks.read_all(session, id, user_id)
    if chunks is None:
        raise HTTPException(status_code=404, detail="Video chunks not found")
    return [(chunk.start_time, chunk.end_time) for chunk in chunks]


@router.put(
    "/start",
    summary="Start source"
)
async def start(session: SessionDep,
                source_processor: SourceProcessorDep,
                user_id: UserIdDep,
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
    source = await crud.sources.read(session, id, user_id)
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
async def pause(session: SessionDep,
                source_processor: SourceProcessorDep,
                user_id: UserIdDep,
                id: int):
    """
    Pause source processing.

    Parameters:
    - **id**: source id
    """
    source = await crud.sources.read(session, id, user_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code != SourceStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Source not active")
    if source.status_code == SourceStatus.FINISHED:
        raise HTTPException(status_code=400, detail="Source already finished")
    print(source_processor.tasks)
    await source_processor.remove(id)
    print(source_processor.tasks)
    await crud.sources.update_status(session, id, SourceStatus.PAUSED)


@router.put(
    "/finish",
    summary="Finish source"
)
async def finish(session: SessionDep,
                 source_processor: SourceProcessorDep,
                 user_id: UserIdDep,
                 id: int):
    """
    Finish source processing. Finished source can't be started again.
    If you create source from file, it will be automatically set as finished,
    upon completion of processing.

    Parameters:
    - **id**: source id
    """
    source = await crud.sources.read(session, id, user_id)
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
async def delete(session: SessionDep,
                 source_processor: SourceProcessorDep,
                 user_id: UserIdDep,
                 id: int):
    """
    Remove source.
    Video chunks will be deleted from disk and database.
    If source was created from file, it will be deleted from disk.
    """
    source = await crud.sources.read(session, id, user_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status_code == SourceStatus.ACTIVE:
        await source_processor.remove(id)
    await crud.sources.delete(session, id)  # Chunks are deleted by cascade
    if source.url.startswith('file://'):  # Delete source file if local
        path = Path(source.url[7:])
        path.unlink()
    shutil.rmtree(settings.chunks_dir / str(id))  # Delete video chunks
