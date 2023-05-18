from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
import cv2

from common.schemas import Source
from app.api_client import session as api_client_session
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


app = FastAPI(
    title="Security Video Retrieval Core API",
    description=description,
    version="0.2.1",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/mit-license.php"
    }
)


source_processor = SourceProcessor()


@app.on_event("startup")
async def startup():
    await api_client_session.startup()
    await source_processor.startup()


@app.on_event("shutdown")
async def shutdown():
    await source_processor.shutdown()
    await api_client_session.shutdown()


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint, redirects to docs"""
    return RedirectResponse(url="/docs")


@app.post(
    "/add",
    summary="Add source to processing list"
)
async def add(source: Source):
    """
    Add source to processing list.

    Parameters:
    - id: source id
    """
    source_processor.add(source)


@app.delete(
    "/remove",
    summary="Remove source from processing list"
)
async def remove(source_id: int):
    """
    Add source to processing list.

    Parameters:
    - id: source id
    """
    await source_processor.remove(source_id)
