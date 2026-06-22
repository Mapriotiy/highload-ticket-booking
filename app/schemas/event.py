import uuid
from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    created_at: datetime


class PerformanceResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    venue_id: uuid.UUID
    starts_at: datetime