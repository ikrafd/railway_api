from fastapi import APIRouter, HTTPException, status, Query
from datetime import date
from app.models import TripSchema
from app.database import create_trip, get_trips_between_stations
from cache import cached_async

trips_router = APIRouter(prefix="/trips", tags=["trips"])

@trips_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_trip(trip: TripSchema):
    try:
        new_trip = await create_trip(trip)
        return new_trip
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@trips_router.get("/", status_code=status.HTTP_200_OK)
@cached_async(expire=60)
async def list_trips(
    departure_station: int = Query(..., description="Код станції відправлення"),
    arrival_station: int = Query(..., description="Код станції прибуття"),
    departure_date: date = Query(..., description="Дата відправлення")
):
    try:
        trips = await get_trips_between_stations(departure_station, arrival_station, departure_date)
        return trips
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
