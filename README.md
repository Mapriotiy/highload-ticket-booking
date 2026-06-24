# Highload Ticket Booking API

Backend project that demonstrates how to handle ticket reservations under concurrent load.

The main goal is to show the difference between a naive booking implementation and a safe implementation that prevents double booking with PostgreSQL row-level locking.

## What This Project Demonstrates

- Ticket reservation flow for events and performances
- Race condition demo with a naive reservation endpoint
- Double booking prevention with `SELECT ... FOR UPDATE`
- Redis cache for performance availability
- Cache invalidation after reservation changes
- Expired reservation cleanup with a background worker
- Docker-based local environment with PostgreSQL and Redis
- Alembic migrations and seed data

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 async ORM
- PostgreSQL 16
- Redis 7
- Alembic
- Docker Compose
- HTTPX for load-test scripts
- Pytest

## Architecture

```text
Client / Load Tests
        |
        v
FastAPI application
        |
        +-- PostgreSQL
        |     - users
        |     - venues
        |     - events
        |     - performances
        |     - seats
        |     - ticket_inventory
        |     - reservations
        |     - reservation_items
        |     - orders
        |     - tickets
        |
        +-- Redis
              - cached performance availability
```

The central table is `ticket_inventory`. Each row represents one sellable seat for one performance.

Important fields:

- `performance_id`
- `seat_id`
- `status`: `available`, `held`, `booked`
- `reservation_id`
- `version`
- `hold_expires_at`

## Reservation Flow

1. A client selects one or more available seats.
2. The API creates a pending reservation.
3. Selected inventory rows are moved from `available` to `held`.
4. The reservation can be confirmed.
5. Confirmation creates an order and tickets.
6. Inventory rows are moved from `held` to `booked`.
7. Pending reservations can be cancelled or expired by the worker.

## Concurrency Strategy

The project contains two reservation implementations.

### Naive Reservation

Endpoint:

```text
POST /reservations/demo/naive
```

This endpoint checks that seats are available and then updates them without locking the selected rows. Under concurrent requests, several transactions can read the same seat as available and create duplicated reservation items.

This endpoint is intentionally unsafe and exists only to demonstrate the race condition.

### Safe Reservation

Endpoint:

```text
POST /reservations
```

This endpoint locks selected `ticket_inventory` rows inside the transaction:

```python
select(TicketInventory)
    .where(...)
    .order_by(TicketInventory.seat_id)
    .with_for_update()
```

Only one transaction can reserve the same seat. Competing requests receive `409 Conflict`.

## API Endpoints

```text
GET  /health
GET  /health/db

GET  /events
GET  /events/{event_id}/performances
GET  /performances/{performance_id}/availability

POST /reservations
POST /reservations/demo/naive
POST /reservations/{reservation_id}/confirm
POST /reservations/{reservation_id}/cancel
```

Interactive API docs are available at:

```text
http://127.0.0.1:8000/docs
```

## How To Run Locally

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL and Redis:

```powershell
docker compose up -d postgres redis
```

Apply migrations:

```powershell
alembic upgrade head
```

Seed demo data:

```powershell
python -m scripts.seed
```

Run the API:

```powershell
python -m uvicorn app.main:app --reload
```

Check health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/health/db
```

## Docker Compose

The project can also be started with Docker Compose:

```powershell
docker compose up --build
```

Services:

- `api`: FastAPI application
- `worker`: expired reservation cleanup worker
- `postgres`: PostgreSQL 16
- `redis`: Redis 7

PostgreSQL is exposed on local port `5433`.

Redis is exposed on local port `6379`.

## Load Testing

Load-test scripts are stored in:

```text
load_tests/
```

Before each race-condition test, reset the database to get clean results:

```powershell
docker compose down -v
docker compose up -d postgres redis
alembic upgrade head
python -m scripts.seed
```

Run the API in another terminal:

```powershell
python -m uvicorn app.main:app --reload
```

### Redis Availability Cache

Command:

```powershell
python -m load_tests.availability_cache
```

Result:

```text
Before reservation:
first cached: False
second cached: True
third cached: True

Reservation status code: 200

After reservation:
after reservation cached: False
next request cached: True
available: 999
held: 1
booked: 0
```

This shows that repeated availability requests are served from Redis, and reservation changes invalidate the cache.

### Safe Reservation Under Load

Command:

```powershell
python -m load_tests.locked_race
```

Result:

```text
Locked reservation race test
----------------------------
status codes: Counter({409: 49, 200: 1})
reservation_items for selected seat: 1
result: no duplicate booking
```

Only one request reserves the selected seat. All competing requests are rejected with `409 Conflict`.

### Naive Reservation Race Condition

Command:

```powershell
python -m load_tests.naive_race
```

Result:

```text
Naive reservation race test
---------------------------
status codes: Counter({409: 35, 200: 15})
reservation_items for selected seat: 15
result: duplicate booking detected
```

The naive endpoint creates multiple reservation items for the same seat. This demonstrates the race condition that the safe endpoint prevents.

## Expired Reservation Worker

Pending reservations have an expiration time. Expired reservations can be released by running:

```powershell
python -m scripts.expire_reservations
```

For continuous cleanup:

```powershell
python -m scripts.expire_worker
```

The Docker Compose `worker` service runs the continuous cleanup process.

## Tests

Run tests:

```powershell
pytest
```

## Project Status

Implemented:

- FastAPI application structure
- PostgreSQL schema with Alembic migrations
- Seed script with demo venue, event, performance, seats, and inventory
- Naive reservation endpoint
- Safe reservation endpoint with row-level locking
- Reservation confirmation
- Reservation cancellation
- Expiration worker
- Redis availability cache
- Load-test scripts for race-condition demonstration

Possible future improvements:

- Authentication and user accounts
- Payment provider integration
- Idempotency keys for payment confirmation
- More detailed test coverage
- Metrics with Prometheus
- Distributed task queue for production-grade background jobs
