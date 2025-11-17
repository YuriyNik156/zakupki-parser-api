from sqlalchemy.orm import Session
from . import models


def create_purchase(db: Session, item: dict):
    db_item = models.Purchase(**item)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_purchases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Purchase).offset(skip).limit(limit).all()
