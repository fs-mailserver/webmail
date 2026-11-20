import logging

import anyio

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import get_engine
from app.core.redis import get_redis
from app.schemas.common import HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])

CHECK_TIMEOUT_SECONDS = 3


@router.get("", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=ReadinessResponse, responses={503: {"model": ReadinessResponse}})
async def readiness(response: Response) -> ReadinessResponse:
    database_ok = redis_ok = True
    try:
        with anyio.fail_after(CHECK_TIMEOUT_SECONDS):
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Readiness: database check failed")
        database_ok = False
    try:
        with anyio.fail_after(CHECK_TIMEOUT_SECONDS):
            await get_redis().ping()
    except Exception:
        logger.exception("Readiness: redis check failed")
        redis_ok = False
    healthy = database_ok and redis_ok
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ok" if healthy else "degraded",
        database="ok" if database_ok else "error",
        redis="ok" if redis_ok else "error",
    )
