from sqlalchemy.orm import Session
from . import models, schemas


def create_purchase(db: Session, item: schemas.PurchaseCreate):
    db_item = models.Purchase(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_purchases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Purchase).offset(skip).limit(limit).all()
