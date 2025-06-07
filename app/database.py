import os
from pathlib import Path
import dotenv
import traceback
import asyncpg
from app.models import StationSchema, TripSchema

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(BASE_DIR / ".env")

async def get_connection():
    try:
        return await asyncpg.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
    except Exception as e:
        print("Database connection error:")
        traceback.print_exc()
        raise


async def create_tables():
    try:
        conn = await get_connection()
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS stations (
                code INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS trains (
                train_number VARCHAR(4) PRIMARY KEY
            );

            CREATE TABLE IF NOT EXISTS wagons (
                id SERIAL PRIMARY KEY,
                train_number VARCHAR(4) REFERENCES trains(train_number),
                wagon_number VARCHAR(2) NOT NULL,
                wagon_class CHAR(1) NOT NULL,
                UNIQUE (train_number, wagon_number)
            );

            CREATE TABLE IF NOT EXISTS trips (
                id SERIAL PRIMARY KEY,
                train_number VARCHAR(4) REFERENCES trains(train_number),
                departure_station INT REFERENCES stations(code),
                arrival_station INT REFERENCES stations(code),
                departure_time TIMESTAMPTZ NOT NULL,
                arrival_time TIMESTAMPTZ NOT NULL,
                CHECK (arrival_time >= departure_time),
                CHECK (departure_station <> arrival_station)
            );

            """)
        await conn.close()
        print("Tables are created successfully...")
    except Exception as e:
        print(f"Error during table creation: {e}")
        traceback.print_exc()
        raise

async def drop_tables():
    conn = await get_connection()
    await conn.execute("""
        DROP TABLE IF EXISTS trips CASCADE;
        DROP TABLE IF EXISTS wagons CASCADE;
        DROP TABLE IF EXISTS trains CASCADE;
        DROP TABLE IF EXISTS stations CASCADE;
    """)
    await conn.close()
    print("Tables are dropped...")


# SELECT

async def get_stations():
    conn = await get_connection()
    rows = await conn.fetch("SELECT * FROM stations;")
    await conn.close()
    return [dict(row) for row in rows]

async def get_station_by_code(code: int):
    conn = await get_connection()
    row = await conn.fetchrow("SELECT name FROM stations WHERE code = $1;", code)
    await conn.close()
    return row["name"] if row else None

async def get_train(train_number: str):
    conn = await get_connection()
    try:
        rows = await conn.fetch("""
            SELECT CONCAT(wagon_number, wagon_class) AS wagon_full
            FROM wagons
            WHERE train_number = $1
            ORDER BY wagon_number;
        """, train_number)
        
        wagons = [row["wagon_full"] for row in rows]
        
        return {
            "train_number": train_number,
            "wagons": wagons
        }
    finally:
        await conn.close()

async def get_trips_between_stations(departure_station, arrival_station, departure_date):
    conn = await get_connection()
    rows = await conn.fetch("""
        SELECT id, train_number, departure_station, arrival_station, departure_time, arrival_time
        FROM trips
        WHERE departure_station = $1 AND arrival_station = $2 AND departure_time::date = $3
        ORDER BY departure_time
    """, departure_station, arrival_station, departure_date)
    await conn.close()
    return [dict(row) for row in rows]


#INSERT 

async def insert_station(payload: StationSchema):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO stations (code, name)
            VALUES ($1, $2)
            RETURNING code, name;
        """, payload.code, payload.name)
        return dict(row)
    except Exception:
        raise
    finally:
        await conn.close()


async def create_train(train_number: str, wagons: list[str]):
    conn = await get_connection()
    try:
        async with conn.transaction():
            await conn.execute("""
                INSERT INTO trains (train_number) VALUES ($1)
            """, train_number)
            for wagon in wagons:
                await conn.execute("""
                    INSERT INTO wagons (train_number, wagon_number, wagon_class)
                    VALUES ($1, $2, $3)
                """, train_number, wagon[:2], wagon[2])
        return {"train_number": train_number, "wagons": wagons}
    finally:
        await conn.close()

async def add_wagons(train_number: str, wagons: list[str]):
    conn = await get_connection()
    try:
        async with conn.transaction():
            for wagon in wagons:
                await conn.execute("""
                    INSERT INTO wagons (train_number, wagon_number, wagon_class)
                    VALUES ($1, $2, $3)
                """, train_number, wagon[:2], wagon[2])
        return {"train_number": train_number, "wagons": wagons}
    finally:
        await conn.close()

async def create_trip(payload: TripSchema):
    conn = await get_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO trips (train_number, departure_station, arrival_station, departure_time, arrival_time)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, train_number, departure_station, arrival_station, departure_time, arrival_time
        """, payload.train_number, payload.departure_station, payload.arrival_station, payload.departure_time, payload.arrival_time)
        return dict(row)
    finally:
        await conn.close()


# DELETE

async def remove_wagons(train_number: str, wagons: list[str]):
    conn = await get_connection()
    try:
        async with conn.transaction():
            for wagon in wagons:
                await conn.execute("""
                    DELETE FROM wagons
                    WHERE train_number = $1 AND wagon_number = $2 AND wagon_class = $3
                """, train_number, wagon[:2], wagon[2])
        return {"train_number": train_number, "removed": wagons}
    finally:
        await conn.close()

