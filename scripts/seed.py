import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.session import async_session_factory
from app.models import Event, Performance, Seat, TicketInventory, User, Venue


DEMO_USER_EMAIL = "demo@example.com"
DEMO_VENUE_NAME = "Chisinau Arena"
DEMO_EVENT_TITLE = "Rock Night"


async def get_or_create_user(session) -> User:
    result = await session.execute(
        select(User).where(User.email == DEMO_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    user = User(
        email=DEMO_USER_EMAIL,
        full_name="Demo User",
    )
    session.add(user)
    await session.flush()

    return user


async def get_or_create_venue(session) -> Venue:
    result = await session.execute(
        select(Venue).where(Venue.name == DEMO_VENUE_NAME)
    )
    venue = result.scalar_one_or_none()

    if venue is not None:
        return venue

    venue = Venue(
        name=DEMO_VENUE_NAME,
        city="Chisinau",
        address="Main Street 1",
    )
    session.add(venue)
    await session.flush()

    return venue


async def get_or_create_event(session) -> Event:
    result = await session.execute(
        select(Event).where(Event.title == DEMO_EVENT_TITLE)
    )
    event = result.scalar_one_or_none()

    if event is not None:
        return event

    event = Event(
        title=DEMO_EVENT_TITLE,
        description="Demo event for ticket booking load testing.",
    )
    session.add(event)
    await session.flush()

    return event


async def get_or_create_performance(session, event: Event, venue: Venue) -> Performance:
    starts_at = datetime.now(timezone.utc) + timedelta(days=30)

    result = await session.execute(
        select(Performance).where(
            Performance.event_id == event.id,
            Performance.venue_id == venue.id,
        )
    )
    performance = result.scalar_one_or_none()

    if performance is not None:
        return performance

    performance = Performance(
        event_id=event.id,
        venue_id=venue.id,
        starts_at=starts_at,
    )
    session.add(performance)
    await session.flush()

    return performance


async def create_seats_if_needed(session, venue: Venue) -> list[Seat]:
    result = await session.execute(
        select(Seat).where(Seat.venue_id == venue.id)
    )
    existing_seats = list(result.scalars().all())

    if existing_seats:
        return existing_seats

    seats: list[Seat] = []

    sections = [chr(code) for code in range(ord("A"), ord("J") + 1)]

    for section in sections:
        for row_number in range(1, 11):
            for seat_number in range(1, 11):
                seat = Seat(
                    venue_id=venue.id,
                    section=section,
                    row=str(row_number),
                    number=seat_number,
                )
                seats.append(seat)

    session.add_all(seats)
    await session.flush()

    return seats


async def create_inventory_if_needed(
    session,
    performance: Performance,
    seats: list[Seat],
) -> None:
    result = await session.execute(
        select(TicketInventory).where(
            TicketInventory.performance_id == performance.id
        )
    )
    existing_inventory = list(result.scalars().all())

    if existing_inventory:
        return

    inventory_items = [
        TicketInventory(
            performance_id=performance.id,
            seat_id=seat.id,
            status="available",
            price_cents=5000,
        )
        for seat in seats
    ]

    session.add_all(inventory_items)
    await session.flush()


async def seed() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            user = await get_or_create_user(session)
            venue = await get_or_create_venue(session)
            event = await get_or_create_event(session)
            performance = await get_or_create_performance(session, event, venue)
            seats = await create_seats_if_needed(session, venue)
            await create_inventory_if_needed(session, performance, seats)

        print("Seed completed")
        print(f"User: {user.email}")
        print(f"Venue: {venue.name}")
        print(f"Event: {event.title}")
        print(f"Performance ID: {performance.id}")
        print(f"Seats: {len(seats)}")


if __name__ == "__main__":
    asyncio.run(seed())