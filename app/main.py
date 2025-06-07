from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from app.database import drop_tables, create_tables
from app.routers.stations import stations_router
from app.routers.trains import trains_router
from app.routers.trips import trips_router

app = FastAPI()

@app.post('/initdb')
async def initdb():
    try:
        create_tables()
        return {"message": "Tables created!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error {e}"
        )

app.include_router(stations_router)
app.include_router(trains_router)
app.include_router(trips_router)