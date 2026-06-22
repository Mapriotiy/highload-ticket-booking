from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import Reservation, TicketInventory
from app.services.availability import invalidate_availability_cache


async def expire_reservations(batch_size: int = 100) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    affected_performance_ids = set()

    async with async_session_factory() as session:
        async with session.begin():
            result = await session.execute(
                select(Reservation)
                .where(
                    Reservation.status == "pending",
                    Reservation.expires_at <= now,
                )
                .order_by(Reservation.expires_at)
                .limit(batch_size)
                .with_for_update(skip_locked=True)
            )
            reservations = list(result.scalars().all())

            expired_count = 0
            released_items = 0

            for reservation in reservations:
                inventory_result = await session.execute(
                    select(TicketInventory)
                    .where(TicketInventory.reservation_id == reservation.id)
                    .order_by(TicketInventory.seat_id)
                    .with_for_update(skip_locked=True)
                )
                inventory_items = list(inventory_result.scalars().all())

                for item in inventory_items:
                    if item.status == "held":
                        affected_performance_ids.add(item.performance_id)
                        item.status = "available"
                        item.reservation_id = None
                        item.hold_expires_at = None
                        item.version += 1
                        released_items += 1

                reservation.status = "expired"
                expired_count += 1

    for performance_id in affected_performance_ids:
        await invalidate_availability_cache(performance_id)

    return expired_count, released_items
