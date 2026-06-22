import uuid

from pydantic import BaseModel


class PerformanceAvailabilityResponse(BaseModel):
    performance_id: uuid.UUID
    available: int
    held: int
    booked: int
    total: int
    cached: bool 
