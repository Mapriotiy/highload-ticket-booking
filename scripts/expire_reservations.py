import asyncio

from app.services.expiration import expire_reservations


async def main() -> None:
    expired_count, released_items = await expire_reservations()

    print(f"Expired reservations: {expired_count}")
    print(f"Released items: {released_items}")


if __name__ == "__main__":
    asyncio.run(main())
