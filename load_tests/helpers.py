import os
from collections import Counter

import httpx
from sqlalchemy import func, select

from app.db.session import async_session_factory
from app.models import Performance, ReservationItem, TicketInventory


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


async def get_available_seat():
    async with async_session_factory() as session:
        result = await session.execute(
            select(TicketInventory.performance_id, TicketInventory.seat_id)
            .where(TicketInventory.status == "available")
            .order_by(TicketInventory.id)
            .limit(1)
        )

        row = result.first()

        if row is None:
            raise RuntimeError("No available seats. Reset DB or run seed script.")

        return str(row.performance_id), str(row.seat_id)


async def get_performance_id():
    async with async_session_factory() as session:
        result = await session.execute(
            select(Performance.id)
            .order_by(Performance.starts_at)
            .limit(1)
        )

        performance_id = result.scalar_one_or_none()

        if performance_id is None:
            raise RuntimeError("No performances. Run seed script first.")

        return str(performance_id)


async def count_reservation_items_for_seat(seat_id: str) -> int:
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count(ReservationItem.id))
            .join(
                TicketInventory,
                TicketInventory.id == ReservationItem.ticket_inventory_id,
            )
            .where(TicketInventory.seat_id == seat_id)
        )

        return result.scalar_one()


async def post_reservation(path: str, performance_id: str, seat_id: str) -> int:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{BASE_URL}{path}",
            json={
                "performance_id": performance_id,
                "seat_ids": [seat_id],
            },
        )

        return response.status_code


def print_result(title: str, statuses: list[int], duplicate_count: int) -> None:
    print()
    print(title)
    print("-" * len(title))
    print("status codes:", Counter(statuses))
    print("reservation_items for selected seat:", duplicate_count)

    if duplicate_count > 1:
        print("result: duplicate booking detected")
    else:
        print("result: no duplicate booking")