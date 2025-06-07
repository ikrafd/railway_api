from fastapi import APIRouter, HTTPException, status
from app.models import TrainWithWagonsSchema, WagonsListSchema
from app.database import get_train, create_train, add_wagons, remove_wagons
from cache import cached_async 

trains_router = APIRouter(prefix="/trains", tags=["trains"])

@trains_router.post("/", status_code=status.HTTP_201_CREATED)
async def create_new_train(payload: TrainWithWagonsSchema):
    try:
        train = await create_train(payload.train_number, payload.wagons)
        return train
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@trains_router.get("/{train_number}", status_code=status.HTTP_200_OK)
@cached_async(expire=60)
async def get_train_by_number(train_number: str):
    train = await get_train(train_number)
    if not train or not train.get("wagons"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Train with number {train_number} not found or has no wagons"
        )
    return train

@trains_router.put("/{train_number}/wagons/add", status_code=status.HTTP_200_OK)
async def add_new_wagons(train_number: str, request: WagonsListSchema):
    try:
        updated_train = await add_wagons(train_number, request.wagons)
        return updated_train
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@trains_router.delete("/{train_number}/wagons", status_code=status.HTTP_200_OK)
async def remove_some_wagons(train_number: str, request: WagonsListSchema):
    try:
        updated_train = await remove_wagons(train_number, request.wagons)
        return updated_train
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
