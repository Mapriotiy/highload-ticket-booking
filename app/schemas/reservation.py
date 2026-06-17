import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateReservationRequest(BaseModel):
    performance_id: uuid.UUID
    seat_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)


class ReservationItemResponse(BaseModel):
    ticket_inventory_id: uuid.UUID
    seat_id: uuid.UUID
    price_cents: int


class ReservationResponse(BaseModel):
    id: uuid.UUID
    status: str
    expires_at: datetime
    items: list[ReservationItemResponse]