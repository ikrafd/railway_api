from fastapi import APIRouter, HTTPException, status
from app.models import StationSchema
from app.database import insert_station, get_station_by_code, get_stations
from fastapi_cache.decorator import cache
from cache import cached_async

stations_router = APIRouter(prefix="/stations", tags=["stations"])

@stations_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_station(payload: StationSchema):
    res = await insert_station(payload)
    return res

@stations_router.get("/", status_code=status.HTTP_200_OK)
@cached_async(expire=60)
async def read_stations():
    stations = await get_stations()
    return stations

@stations_router.get("/{code}", status_code=status.HTTP_200_OK)
@cached_async(expire=60)
async def read_station(code: int):
    station = await get_station_by_code(code)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station
