import json
import uuid

from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis import redis_client
from app.models import TicketInventory

CACHE_TTL_SECONDS = 10


def availability_cache_key(performance_id: uuid.UUID) -> str:
    return f"availability:{performance_id}"

async def invalidate_availability_cache(performance_id: uuid.UUID) -> None:
    try:
        await redis_client.delete(availability_cache_key(performance_id))
    except RedisError:
        pass

async def get_performance_availability(
    session: AsyncSession,
    performance_id: uuid.UUID,
) -> dict:
    cache_key = availability_cache_key(performance_id)

    try:
        cached = await redis_client.get(cache_key)
    except RedisError:
        cached = None

    if cached is not None:
        data = json.loads(cached)
        data["cached"] = True
        return data

    result = await session.execute(
        select(TicketInventory.status, func.count())
        .where(TicketInventory.performance_id == performance_id)
        .group_by(TicketInventory.status)
    )

    counts = {
        "available": 0,
        "held": 0,
        "booked": 0,
    }

    for status, count in result.all():
        counts[status] = count

    data = {
        "performance_id": str(performance_id),
        "available": counts["available"],
        "held": counts["held"],
        "booked": counts["booked"],
        "total": sum(counts.values()),
        "cached": False,
    }

    try:
        await redis_client.set(
            cache_key,
            json.dumps(data),
            ex=CACHE_TTL_SECONDS,
        )
    except RedisError:
        pass

    return data



