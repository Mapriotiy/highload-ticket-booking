import asyncio

from load_tests.helpers import (
    count_reservation_items_for_seat,
    get_available_seat,
    post_reservation,
    print_result,
)


CONCURRENT_REQUESTS = 50


async def main():
    performance_id, seat_id = await get_available_seat()

    print("performance_id:", performance_id)
    print("seat_id:", seat_id)

    tasks = [
        post_reservation(
            path="/reservations/demo/naive",
            performance_id=performance_id,
            seat_id=seat_id,
        )
        for _ in range(CONCURRENT_REQUESTS)
    ]

    statuses = await asyncio.gather(*tasks)

    duplicate_count = await count_reservation_items_for_seat(seat_id)

    print_result(
        title="Naive reservation race test",
        statuses=statuses,
        duplicate_count=duplicate_count,
    )


if __name__ == "__main__":
    asyncio.run(main())