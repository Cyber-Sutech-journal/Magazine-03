from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Seat, Booking
from app.models.user import User
from app.schemas.booking import SeatOut, BookingCreate, BookingOut
from app.auth.jwt_handler import get_current_user

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


@router.get(
    "/showtimes/{showtime_id}/seats",
    response_model=list[SeatOut],
    summary="View seat availability for a showtime",
    description=(
        "Returns every seat in the hall for the given showtime, "
        "along with its status: 'available' or 'booked'. "
        "Status is computed based on existing bookings for that "
        "specific showtime, not stored directly on the seat. "
        "No authentication required."
    )
)
def get_seats_for_showtime(
    showtime_id: int,
    db: Session = Depends(get_db)
):
    seats = db.query(Seat).all()

    booked_seat_ids = {
        b.seat_id for b in db.query(Booking).filter(
            Booking.showtime_id == showtime_id
        ).all()
    }

    result = []
    for seat in seats:
        status_value = "booked" if seat.id in booked_seat_ids else "available"
        result.append(
            SeatOut(id=seat.id, seat_number=seat.seat_number, status=status_value)
        )

    return result


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingOut,
    summary="Book a seat",
    description=(
        "Creates a new booking for the current authenticated user, "
        "for a given showtime and seat. The user is identified from "
        "the JWT token, not from the request body. "
        "Returns 409 Conflict if the seat is already booked for that showtime."
    )
)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_booking = db.query(Booking).filter(
        Booking.showtime_id == booking_data.showtime_id,
        Booking.seat_id == booking_data.seat_id
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This seat is already booked for this showtime"
        )

    new_booking = Booking(
        user_id=current_user.id,
        showtime_id=booking_data.showtime_id,
        seat_id=booking_data.seat_id,
        status="confirmed"
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking


@router.get(
    "/me",
    response_model=list[BookingOut],
    summary="List the current user's bookings",
    description="Returns all bookings made by the currently authenticated user, identified from the JWT token."
)
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Booking).filter(Booking.user_id == current_user.id).all()


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a booking",
    description=(
        "Cancels (deletes) a booking by id. Only the user who made the "
        "booking may cancel it. Returns 404 if the booking does not exist, "
        "and 403 if the current user does not own it."
    )
)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to cancel this booking"
        )

    db.delete(booking)
    db.commit()
    return None