from sqlalchemy.orm import Session
from . import models
from .models import Purchase


def create_purchase(db: Session, data: dict):
    existing = get_purchase_by_number(db, data["number"])
    if existing:
        return existing  # возвращаем уже существующий объект

    new_purchase = Purchase(**data)
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase


def get_purchases(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Purchase).offset(skip).limit(limit).all()

def get_purchase_by_number(db: Session, number: str):
    return db.query(Purchase).filter(Purchase.number == number).first()
