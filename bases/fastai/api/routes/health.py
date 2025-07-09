from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import text
import structlog.stdlib

from fastai.api.depenedencies import SessionDep

router = APIRouter(tags=["health"])

logger = structlog.get_logger(__name__)


@router.get("/livez")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/readyz", response_class=JSONResponse)
async def database_health_check(session: SessionDep):
    """Health check that verifies database connectivity."""
    try:
        # Simple query to test database connectivity
        result = await session.exec(text("SELECT 1 as test"))
        row = result.fetchone()

        if row and row[0] == 1:
            return {"status": "ready"}
        else:
            return {"status": "not ready"}
    except Exception:
        logger.exception("Error in database health check")
        return {"status": "not ready"}
