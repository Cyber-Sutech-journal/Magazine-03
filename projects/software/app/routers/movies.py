from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.movie import Movie, Hall, Showtime
from app.schemas.movie import (
    MovieCreate,
    MovieResponse,
    ShowtimeCreate,
    ShowtimeResponse
)
from app.auth.jwt_handler import get_current_user

router = APIRouter(
    tags=["Movies"]
)


@router.post(
    "/movies",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie",
    description=(
        "Adds a new movie to the catalog. Requires authentication, "
        "and only users with the 'admin' role are allowed to perform "
        "this action. Returns 403 if the current user is not an admin."
    )
)
def create_movie(
    movie: MovieCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create movies"
        )
    new_movie = Movie(
        title=movie.title,
        duration=movie.duration
    )
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@router.get(
    "/movies",
    response_model=list[MovieResponse],
    summary="List all movies",
    description="Returns the full list of movies currently in the catalog. No authentication required."
)
def get_movies(
    db: Session = Depends(get_db)
):
    movies = db.query(Movie).all()
    return movies


@router.post(
    "/showtimes",
    response_model=ShowtimeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new showtime",
    description=(
        "Schedules a new showtime for an existing movie in an existing hall. "
        "Requires authentication and the 'admin' role. "
        "Returns 404 if the referenced movie or hall does not exist, "
        "and 403 if the current user is not an admin."
    )
)
def create_showtime(
    showtime: ShowtimeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create showtimes"
        )
    movie = db.query(Movie).filter(
        Movie.id == showtime.movie_id
    ).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    hall = db.query(Hall).filter(
        Hall.id == showtime.hall_id
    ).first()
    if not hall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hall not found"
        )
    new_showtime = Showtime(
        movie_id=showtime.movie_id,
        hall_id=showtime.hall_id,
        start_time=showtime.start_time
    )
    db.add(new_showtime)
    db.commit()
    db.refresh(new_showtime)
    return new_showtime


@router.get(
    "/movies/{movie_id}/showtimes",
    response_model=list[ShowtimeResponse],
    summary="List showtimes for a movie",
    description=(
        "Returns all scheduled showtimes for a specific movie, "
        "identified by its id. Returns 404 if the movie does not exist."
    )
)
def get_movie_showtimes(
    movie_id: int,
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(
        Movie.id == movie_id
    ).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    showtimes = db.query(Showtime).filter(
        Showtime.movie_id == movie_id
    ).all()
    return showtimes