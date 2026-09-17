"""FastAPI surface for the PatchPilot release-memory demo."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated

from azure.core.exceptions import AzureError
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from patchpilot import PatchPilotService
from patchpilot.telemetry import configure_telemetry

logger = configure_telemetry()
service = PatchPilotService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        service.initialize_cloud()
        logger.info("PatchPilot cloud adapters initialized")
    except Exception:
        logger.exception("PatchPilot cloud initialization failed")
    yield


app = FastAPI(
    title="PatchPilot release memory",
    version="1.0.0",
    lifespan=lifespan,
)


class QueryRequest(BaseModel):
    persona: str = "release-engineer"
    question: str
    strategy: str = "guarded"


@app.get("/health")
def health() -> dict[str, object]:
    state = service.state()
    cloud = state["cloud"]
    return {
        "status": "healthy" if not cloud["enabled"] or cloud["ready"] else "degraded",
        "cloud": cloud,
    }


@app.get("/demo/state")
def state() -> dict[str, object]:
    return service.state()


@app.post("/demo/reset")
def reset() -> dict[str, object]:
    return service.reset()


@app.post("/demo/unsafe")
def unsafe() -> dict[str, object]:
    return service.run_unsafe().model_dump(mode="json")


@app.post("/demo/guarded")
def guarded() -> dict[str, object]:
    return service.run_guarded().model_dump(mode="json")


@app.post("/demo/rollback")
def rollback() -> dict[str, object]:
    try:
        return service.rollback()
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/query")
def query(
    request: QueryRequest,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, object]:
    try:
        result = service.query(
            request.persona,
            request.question,
            guarded=request.strategy == "guarded",
            query_source_authorization=authorization,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except AzureError as error:
        logger.exception("Azure AI Search query failed")
        raise HTTPException(
            status_code=502,
            detail=f"Azure AI Search query failed: {type(error).__name__}",
        ) from error
    result.setdefault("query_source_authorization_forwarded", False)
    result.setdefault("authorization_mode", "local-tenant-and-group-filter")
    return result
