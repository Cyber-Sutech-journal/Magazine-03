# Cinema Booking API

A REST API for browsing movies, checking showtimes, and booking cinema seats — built with **Python** and **FastAPI** as part of the Software section of Cyber Sutech Magazine, Issue 03.

## Overview

Users can register, log in, browse movies and showtimes, view seat availability for a showtime, and book or cancel a seat. Admin users can create movies and showtimes.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (development) |
| Validation | Pydantic |
| Authentication | JWT (via `pyjwt`) |
| Password Hashing | `pwdlib` |
| API Docs | Swagger UI (auto-generated) |

## Project Structure

```
app/
├── main.py                  # Application entry point
├── database.py              # Database engine and session setup
├── models/                  # SQLAlchemy database models
│   ├── user.py
│   ├── movie.py             # Movie, Hall, Showtime
│   └── booking.py           # Seat, Booking
├── schemas/                 # Pydantic request/response schemas
│   ├── user.py
│   ├── movie.py
│   └── booking.py
├── routers/                 # API endpoints
│   ├── auth.py
│   ├── movies.py
│   └── bookings.py
└── auth/
    └── jwt_handler.py       # Password hashing, JWT creation/validation
```

## Setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, with interactive documentation at:

```
http://127.0.0.1:8000/docs
```

## Authentication

Most write operations require a valid JWT. To authenticate:

1. Register a user: `POST /auth/register`
2. Log in to get a token: `POST /auth/login`
3. Include the token in subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```

Two roles exist: `user` (default) and `admin` (required to create movies and showtimes).

## API Endpoints

### Auth
| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in and receive a JWT | No |

### Movies & Showtimes
| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| GET | `/movies` | List all movies | No |
| POST | `/movies` | Create a movie | Admin |
| GET | `/movies/{movie_id}/showtimes` | List showtimes for a movie | No |
| POST | `/showtimes` | Create a showtime | Admin |

### Bookings
| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| GET | `/bookings/showtimes/{showtime_id}/seats` | View seat availability for a showtime | No |
| POST | `/bookings` | Book a seat | Yes |
| GET | `/bookings/me` | List the current user's bookings | Yes |
| DELETE | `/bookings/{booking_id}` | Cancel a booking | Yes |

## Example Flow

1. `POST /auth/register` → create an account
2. `POST /auth/login` → get an access token
3. `GET /movies` → browse available movies
4. `GET /movies/{movie_id}/showtimes` → pick a showtime
5. `GET /bookings/showtimes/{showtime_id}/seats` → check which seats are free
6. `POST /bookings` → book a seat
   - Returns **409 Conflict** if the seat is already booked for that showtime
7. `GET /bookings/me` → view your bookings
8. `DELETE /bookings/{booking_id}` → cancel a booking
   - Returns **403 Forbidden** if it's not your booking


## Status

Core functionality (authentication, movie/showtime management, seat booking) is implemented and tested locally. Remaining work includes finalizing API documentation and preparing the live demo.