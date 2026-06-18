import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reservation, ReservationItem, TicketInventory, User, Order, Ticket


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
    unique_seat_ids = list(dict.fromkeys(seat_ids))

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


async def create_reservation_with_lock(
    session: AsyncSession,
    performance_id: uuid.UUID,
    seat_ids: list[uuid.UUID],
) -> tuple[Reservation, list[TicketInventory]]:
    unique_seat_ids = list(dict.fromkeys(seat_ids))

    async with session.begin():
        user = await get_demo_user(session)

        result = await session.execute(
            select(TicketInventory)
            .where(
                TicketInventory.performance_id == performance_id,
                TicketInventory.seat_id.in_(unique_seat_ids),
            )
            .order_by(TicketInventory.seat_id)
            .with_for_update()
        )
        inventory_items = list(result.scalars().all())

        if len(inventory_items) != len(unique_seat_ids):
            raise SeatsNotFoundError("Some seats were not found.")

        if any(item.status != "available" for item in inventory_items):
            raise SeatsUnavailableError("Some seats are not available.")

        reservation = await build_reservation(session, user, inventory_items)

    return reservation, inventory_items


class ReservationNotFoundError(ReservationError):
    pass


class InvalidReservationStateError(ReservationError):
    pass


class ReservationExpiredError(ReservationError):
    pass


def generate_ticket_code() -> str:
    return f"TCK-{uuid.uuid4().hex[:12].upper()}"


async def confirm_reservation(
    session: AsyncSession,
    reservation_id: uuid.UUID,
)-> tuple[Reservation, Order, list[Ticket]]:
    now = datetime.now(timezone.utc)

    async with session.begin():
        result = await session.execute(
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .with_for_update()
        )
        reservation = result.scalar_one_or_none()

        if reservation is None:
            raise ReservationNotFoundError("Reservation not found")

        if reservation.status != "pending":
            raise InvalidReservationStateError(
                f"Reservation cannot be confirmed from status {reservation.status}"
            )

        if reservation.expires_at <= now:
            reservation.status = "expired"
            raise ReservationExpiredError("Reservation expired")

        inventory_result = await session.execute(
            select(TicketInventory)
            .where(TicketInventory.reservation_id == reservation_id)
            .order_by(TicketInventory.seat_id)
            .with_for_update()
        )
        inventory_items = list(inventory_result.scalars().all())

        if not inventory_items:
            raise InvalidReservationStateError("Reservation has no held items.")

        if any(item.status != "held" for item in inventory_items):
            raise InvalidReservationStateError(
                "Reservation contains items that are not held."
            )

        total_cents = sum(item.price_cents for item in inventory_items)

        order = Order(
            user_id=reservation.user_id,
            reservation_id=reservation.id,
            status="paid",
            total_cents=total_cents,
        )
        session.add(order)
        await session.flush()

        tickets: list[Ticket] = []

        for item in inventory_items:
            item.status = "booked"
            item.hold_expires_at = None
            item.version += 1

            ticket = Ticket(
                order_id=order.id,
                ticket_inventory_id=item.id,
                code=generate_ticket_code(),
            )
            session.add(ticket)
            tickets.append(ticket)

        reservation.status = "confirmed"
        reservation.confirmed_at = now

        await session.flush()

    return reservation, order, tickets