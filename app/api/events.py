import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.schemas.event import EventResponse, PerformanceResponse
from app.services.events import list_event_performances, list_events

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventResponse])
async def get_events(session: AsyncSession = Depends(get_db_session)) -> list[EventResponse]:
    return await list_events(session)

@router.get("/events/{event_id}/performances", response_model=list[PerformanceResponse])
async def get_event_performances(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[PerformanceResponse]:
    return await list_event_performances(session, event_id)
