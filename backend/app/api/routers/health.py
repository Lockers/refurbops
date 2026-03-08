from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import ping_database
from app.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    settings = get_settings()
    database = "ok"

    try:
        ping_database()
    except Exception:
        database = "unavailable"

    return HealthResponse(
        ok=True,
        app="refurbops-backend",
        environment=settings.app_env,
        database=database,
    )
