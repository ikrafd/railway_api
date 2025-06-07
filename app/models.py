from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime



class StationSchema(BaseModel):
    code: int = Field(..., description="Код станції")
    name: str = Field(..., min_length=3, max_length=255, description="Назва станції")

    @field_validator('code')
    def code_must_start_with_22(cls, v):
        if not (str(v).startswith("22") and len(str(v)) == 7):
            raise ValueError("Код має бути 7-значним числом, що починається з 22")
        return v

    @field_validator('name')
    def name_valid_chars(cls, v):
        import re
        if not re.match(r"^[а-яА-ЯіїєґІЇЄҐ0-9\-']{3,}$", v):
            raise ValueError("Назва має містити лише кириличні літери, цифри, дефіс і бути не коротшою за 3 символи")
        return v


class TrainSchema(BaseModel):
    train_number: str = Field(..., pattern=r"^\d{3}[А-Яа-яІіЇїЄєҐґ]$", description="Номер потяга")

class WagonSchema(BaseModel):
    wagon_number: str = Field(..., pattern=r"^\d{2}$", description="Двозначний номер вагона")
    wagon_class: str = Field(..., pattern=r"^[КПЛ]$", description="Клас вагона")

class WagonsListSchema(BaseModel):
    wagons: List[str]

    @field_validator('wagons')
    def validate_wagons(cls, v):
        wagon_numbers = set()
        for w in v:
            if not w or len(w) != 3:
                raise ValueError("Кожен вагон має складатись з 3 символів: 2 цифри та 1 літера")
            number, wclass = w[:2], w[2]
            if not number.isdigit():
                raise ValueError("Номер вагона має бути двозначним числом")
            if wclass not in "КПЛ":
                raise ValueError("Клас вагона має бути одним із: К, П, Л")
            if number in wagon_numbers:
                raise ValueError("У поїзді не може бути кількох вагонів з однаковим номером")
            wagon_numbers.add(number)
        if len(v) == 0:
            raise ValueError("Поїзд має містити хоча б один вагон")
        return v

class TrainWithWagonsSchema(WagonsListSchema):
    train_number: str = Field(..., pattern=r"^\d{3}[А-Яа-яІіЇїЄєҐґ]$", description="Номер поїзда")


class TripSchema(BaseModel):
    train_number: str = Field(..., pattern=r"^\d{3}[А-Яа-яІіЇїЄєҐґ]$", description="Номер поїзда")
    departure_station: int = Field(..., description="Код станції відправлення")
    arrival_station: int = Field(..., description="Код станції прибуття")
    departure_time: datetime = Field(..., description="Дата та час відправлення")
    arrival_time: datetime = Field(..., description="Дата та час прибуття")

    @field_validator('arrival_time')
    def arrival_after_departure(cls, v, values):
        departure_time = getattr(values, 'data', {}).get('departure_time')
        if departure_time is not None and v < departure_time:
            raise ValueError("Час прибуття не може бути раніше часу відправлення")
        return v

    @field_validator('arrival_station')
    def arrival_station_differs(cls, v, values):
        departure_station = getattr(values, 'data', {}).get('departure_station')
        if departure_station is not None and v == departure_station:
            raise ValueError("Станція прибуття має відрізнятись від станції відправлення")
        return v


