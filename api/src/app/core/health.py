"""GET /v1/health: liveness only. No database call, so a database outage never becomes a restart
loop (standard §17)."""

from fastapi import APIRouter

from app.core.schemas import ApiModel

router = APIRouter(tags=["health"])


class Health(ApiModel):
    status: str


@router.get("/v1/health")
async def health() -> Health:
    return Health(status="ok")
