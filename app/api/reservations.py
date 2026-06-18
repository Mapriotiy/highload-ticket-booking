from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.dependencies import get_db_session
from app.schemas.reservation import (
    CreateReservationRequest,
    ReservationItemResponse,
    ReservationResponse,
    ConfirmReservationResponse,
)
from app.services.reservations import (
    ReservationError,
    SeatsNotFoundError,
    SeatsUnavailableError,
    create_reservation_naive,
    create_reservation_with_lock,
    ReservationExpiredError,
    ReservationNotFoundError,
    InvalidReservationStateError,
    confirm_reservation,
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


def build_response(reservation, inventory_items) -> ReservationResponse:
    return ReservationResponse(
        id=reservation.id,
        status=reservation.status,
        expires_at=reservation.expires_at,
        items=[
            ReservationItemResponse(
                ticket_inventory_id=item.id,
                seat_id=item.seat_id,
                price_cents=item.price_cents,
            )
            for item in inventory_items
        ],
    )


@router.post("/demo/naive", response_model=ReservationResponse)
async def create_naive_reservation(
    payload: CreateReservationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReservationResponse:
    try:
        reservation, inventory_items = await create_reservation_naive(
            session=session,
            performance_id=payload.performance_id,
            seat_ids=payload.seat_ids,
        )
    except SeatsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SeatsUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ReservationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return build_response(reservation, inventory_items)


@router.post("", response_model=ReservationResponse)
async def create_reservation(
    payload: CreateReservationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReservationResponse:
    try:
        reservation, inventory_items = await create_reservation_with_lock(
            session=session,
            performance_id=payload.performance_id,
            seat_ids=payload.seat_ids,
        )
    except SeatsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SeatsUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ReservationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return build_response(reservation, inventory_items)


@router.post("/{reservation_id}/confirm", response_model=ConfirmReservationResponse)
async def confirm_existing_reservation(
    reservation_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ConfirmReservationResponse:
    try:
        reservation, order, tickets = await confirm_reservation(
            session=session,
            reservation_id=reservation_id,
        )
    except ReservationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (InvalidReservationStateError, ReservationExpiredError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except ReservationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ConfirmReservationResponse(
        reservation_id=reservation.id,
        reservation_status=reservation.status,
        order_id=order.id,
        order_status=order.status,
        total_cents=order.total_cents,
        ticket_count=len(tickets),
    )