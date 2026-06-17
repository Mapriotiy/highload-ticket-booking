import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reservation, ReservationItem, TicketInventory, User


class ReservationError(Exception):
    pass


class SeatsNotFoundError(ReservationError):
    pass


class SeatsUnavailableError(ReservationError):
    pass


async def get_demo_user(session: AsyncSession) -> User:
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if user is None:
        raise ReservationError("Demo user not found. Run seed script first.")

    return user


async def build_reservation(
    session: AsyncSession,
    user: User,
    inventory_items: list[TicketInventory],
) -> Reservation:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    reservation = Reservation(
        user_id=user.id,
        status="pending",
        expires_at=expires_at,
    )
    session.add(reservation)
    await session.flush()

    for item in inventory_items:
        reservation_item = ReservationItem(
            reservation_id=reservation.id,
            ticket_inventory_id=item.id,
            price_cents=item.price_cents,
        )
        session.add(reservation_item)

        item.status = "held"
        item.reservation_id = reservation.id
        item.hold_expires_at = expires_at
        item.version += 1

    await session.flush()

    return reservation


async def create_reservation_naive(
    session: AsyncSession,
    performance_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
) -> tuple[Reservation, list[TicketInventory]]:
    unique_seat_ids = list(set(seat_ids))

    async with session.begin():
        user = await get_demo_user(session)

        result = await session.execute(
            select(TicketInventory).where(
                TicketInventory.performance_id == performance_id,
                TicketInventory.seat_id.in_(unique_seat_ids),
            )
        )
        inventory_items = list(result.scalars().all())

        if len(inventory_items) != len(unique_seat_ids):
            raise SeatsNotFoundError("Some seats were not found.")

        if any(item.status != "available" for item in inventory_items):
            raise SeatsUnavailableError("Some seats are not available.")

        await asyncio.sleep(0.2)

        reservation = await build_reservation(session, user, inventory_items)

    return reservation, inventory_items

