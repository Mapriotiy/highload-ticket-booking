from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db_session
from app.schemas.reservation import (
    CreateReservationRequest,
    ReservationItemResponse,
    ReservationResponse,
)
from app.services.reservations import (
    ReservationError,
    SeatsNotFoundError,
    SeatsUnavailableError,
    create_reservation_naive,
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


