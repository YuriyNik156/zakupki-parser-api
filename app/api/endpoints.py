from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.deps import get_db

router = APIRouter()


@router.post("/purchases/", response_model=schemas.PurchaseResponse)
def create_purchase(item: schemas.PurchaseCreate, db: Session = Depends(get_db)):
    return crud.create_purchase(db, item)


@router.get("/purchases/", response_model=list[schemas.PurchaseResponse])
def list_purchases(db: Session = Depends(get_db)):
    return crud.get_purchases(db)
