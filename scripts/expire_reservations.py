import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import Reservation, TicketInventory


async def expire_reservations() -> tuple[int, int]:
    now = datetime.now(timezone.utc)

    async with async_session_factory() as session:
        async with session.begin():
            result = await session.execute(
                select(Reservation)
                .where(
                    Reservation.status == "pending",
                    Reservation.expires_at <= now,
                )
                .with_for_update()
            )
            reservations = list(result.scalars().all())

            expired_count = 0
            released_items = 0

            for reservation in reservations:
                inventory_result = await session.execute(
                    select(TicketInventory)
                    .where(TicketInventory.reservation_id == reservation.id)
                    .order_by(TicketInventory.seat_id)
                    .with_for_update()
                )
                inventory_items = list(inventory_result.scalars().all())

                for item in inventory_items:
                    if item.status == "held":
                        item.status = "available"
                        item.reservation_id = None
                        item.hold_expires_at = None
                        item.version += 1
                        released_items += 1

                reservation.status = "expired"
                expired_count += 1

        return expired_count, released_items


async def main() -> None:
    expired_count, released_items = await expire_reservations()

    print(f"Expired reservations: {expired_count}")
    print(f"Released items: {released_items}")


if __name__ == "__main__":
    asyncio.run(main())