import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Event(Base):
    __tablename__ = 'events'

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None ] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    perfomances: Mapped[list["Perfomance"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

class Perfomance(Base):
    __tablename__ = 'perfomances'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('events.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('venues.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped[Event] = relationship(
        back_populates="perfomances",
    )
