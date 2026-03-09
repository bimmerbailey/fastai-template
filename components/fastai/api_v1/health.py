import structlog.stdlib
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.responses import PlainTextResponse

from fastai.database.core import health_check
from fastai.utils.dependencies import SessionDep

router = APIRouter(tags=["health"])

logger = structlog.get_logger(__name__)


@router.get("/livez", response_class=PlainTextResponse)
async def livez_health_check():
    """Basic health check endpoint."""
    return "livez"


@router.get("/readyz", response_class=JSONResponse)
async def database_health_check(session: SessionDep):
    """Health check that verifies database connectivity."""
    return await health_check(session=session)
