import asyncio
from collections import Counter

import httpx

URL = "http://127.0.0.1:8000/reservations/demo/naive"

PAYLOAD = {
    "performance_id": "49ef13e4-1b18-415f-a4ad-c0f7b770fe49",
    "seat_ids": ["24b1b67b-afa3-432a-88e9-f1f5767ccf94"],
}

REQUESTS = 50


async def send_request(client: httpx.AsyncClient) -> int:
    response = await client.post(URL, json=PAYLOAD)
    return response.status_code


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = await asyncio.gather(
            *(send_request(client) for _ in range(REQUESTS)),
            return_exceptions=True,
        )

    statuses = Counter(
        result if isinstance(result, int) else type(result).__name__
        for result in results
    )

    print(statuses)


if __name__ == "__main__":
    asyncio.run(main())