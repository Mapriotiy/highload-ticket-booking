import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.schemas.availability import PerformanceAvailabilityResponse
from app.services.availability import get_performance_availability

router = APIRouter(prefix="/performances", tags=["performances"])


@router.get("/{performance_id}/availability", response_model=PerformanceAvailabilityResponse)
async def get_availability(
    performance_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PerformanceAvailabilityResponse:
    return await get_performance_availability(session, performance_id)