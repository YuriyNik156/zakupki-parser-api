from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.deps import get_db
from app.crud import create_purchase, get_purchases
from app.parser.gos_zakupki_parser import get_purchases_selenium


router = APIRouter()


# ---------------------------
#   POST /api/parse
# ---------------------------
@router.post("/parse")
def parse_purchases(
    fz: str = "44",
    pages: int = 3,
    region: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Запускает Selenium-парсер и сохраняет данные в базу.
    """
    data = get_purchases_selenium(
        fz=fz,
        max_pages=pages,
        region=region
    )

    saved = []
    for item in data:
        saved_item = create_purchase(db, item)
        saved.append(saved_item.id)

    return {
        "message": "Парсинг успешно выполнен!",
        "saved_records": len(saved),
        "ids": saved
    }


# ---------------------------
#   GET /api/purchases
# ---------------------------
@router.get("/purchases")
def list_purchases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Возвращает список закупок из базы.
    """
    return get_purchases(db, skip=skip, limit=limit)
