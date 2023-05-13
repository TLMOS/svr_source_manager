from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
import cv2

from app import schemas
from app.video_processing import SourceProcessor


description = """
Source processing service.
Keeps a list of active sources and process them asynchronously.

Source processing steps:
- Get frames from source url
- Save frames to disk as video chunks
- Ask core API to create database records for video chunks
- Send video chunks to RabbitMQ queue
"""


source_processor = SourceProcessor()


app = FastAPI(
    title="Security Video Retrieval Core API",
    description=description,
    version="0.0.1",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/mit-license.php"
    }
)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url="/docs")


@app.post(
    "/add",
    summary="Add source to processing list"
)
async def add(source_schema: schemas.Source):
    """
    Add source to processing list.

    Parameters:
    - **id**: source id
    """
    source_processor.add(source_schema)


@app.delete(
    "/remove",
    summary="Remove source from processing list"
)
async def remove(source_id: int):
    """
    Add source to processing list.

    Parameters:
    - **id**: source id
    """
    await source_processor.remove(source_id)


@app.get(
    "/get_frame",
    summary="Get frame",
    response_description="Frame",
    response_class=Response
)
async def get_frame(source_id: int):
    """
    Get last frame from source

    Parameters:
    - **id**: source id
    """
    frame = source_processor.get_frame(source_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Frame not found")
    _, buffer = cv2.imencode('.jpg', frame)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")
