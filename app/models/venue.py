import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Venue(Base):
    __tablename__ = 'venues'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    seats: Mapped[list["Seat"]] = relationship(
        back_populates="venue",
        cascade="all, delete-orphan",
    )

class Seat(Base):
    __tablename__ = 'seats'

    __table_args__ = (
        UniqueConstraint(
            "venue_id",
            "section",
            "row",
            "number",
            name="uq_seats_venue_section_row_number",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('venues.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    section: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    row: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    venue: Mapped[Venue] = relationship(
        back_populates="seats",
    )