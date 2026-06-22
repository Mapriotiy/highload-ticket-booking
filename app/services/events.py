import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Performance


async def list_events(session: AsyncSession) -> list[Event]:
    result = await session.execute(
        select(Event).order_by(Event.created_at.desc())
    )
    return list(result.scalars().all())


async def list_event_performances(
    session: AsyncSession,
    event_id: uuid.UUID,
) -> list[Performance]:
    result = await session.execute(
        select(Performance)
        .where(Performance.event_id == event_id)
        .order_by(Performance.starts_at)
    )
    return list(result.scalars().all())

