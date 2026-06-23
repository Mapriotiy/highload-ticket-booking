import asyncio

import httpx

from load_tests.helpers import BASE_URL, get_available_seat, get_performance_id, post_reservation


async def get_availability(performance_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{BASE_URL}/performances/{performance_id}/availability"
        )
        response.raise_for_status()
        return response.json()


async def main():
    performance_id = await get_performance_id()

    first = await get_availability(performance_id)
    second = await get_availability(performance_id)
    third = await get_availability(performance_id)

    print("Before reservation:")
    print("first cached:", first["cached"])
    print("second cached:", second["cached"])
    print("third cached:", third["cached"])

    performance_id, seat_id = await get_available_seat()

    status_code = await post_reservation(
        path="/reservations",
        performance_id=performance_id,
        seat_id=seat_id,
    )

    after_reservation = await get_availability(performance_id)
    next_request = await get_availability(performance_id)

    print()
    print("Reservation status code:", status_code)

    print()
    print("After reservation:")
    print("after reservation cached:", after_reservation["cached"])
    print("next request cached:", next_request["cached"])
    print("available:", after_reservation["available"])
    print("held:", after_reservation["held"])
    print("booked:", after_reservation["booked"])


if __name__ == "__main__":
    asyncio.run(main())