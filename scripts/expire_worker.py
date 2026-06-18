import asyncio

from app.services.expiration import expire_reservations


async def main() -> None:
    while True:
        expired_count, released_items = await expire_reservations()

        if expired_count or released_items:
            print(
                f"expired={expired_count}, released={released_items}",
                flush=True,
            )

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
