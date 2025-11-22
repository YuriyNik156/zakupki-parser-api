from threading import Thread, Event
from sqlalchemy.orm import Session
from datetime import datetime

from app.deps import SessionLocal, engine
from app.models import Purchase
from app.parser.gos_zakupki_parser import get_purchases_selenium
from app.crud import create_purchase

# Глобальный stop_event и поток
stop_event = Event()
parser_thread = None

# Настройки парсера
parser_settings = {
    "fz": "44",
    "region": None,
    "price_min": None,
    "price_max": None,
    "date_from": None,
    "date_to": None,
    "max_pages": 3,
    "category": None
}

CATEGORY_KEYWORDS = {
    "техника": ["компьютер", "ноутбук", "оргтех", "принтер", "сканер", "мфу"],
    "лекарства": ["лекарств", "препарат", "фармацевт"],
    "услуги": ["услуги", "перевозк", "дезинфекц", "обслуживан"],
    "мебель": ["мебел", "шкаф", "стол", "тумб"],
    "технические материалы": ["масло", "смазк", "техническ"],
    "медицинские изделия": ["расходн", "медицинск", "издел"],
    "оборудование": ["систем", "станок", "комплекс", "видеонаблюдени"],
    "строительные работы": ["ремонт", "строит"],
    "программное обеспечение": ["программн", "software", "софт", "лиценз", "приложен", "информационн", "ПО"]
}


def filter_by_category(item: dict, category: str) -> bool:
    if not category:
        return True
    subject = item.get("subject", "").lower()
    words = CATEGORY_KEYWORDS.get(category.lower(), [])
    return any(word in subject for word in words)


def run_parser_once():
    """Один запуск парсера."""
    db: Session = SessionLocal()
    print("=== Запуск парсера: однократный режим ===")

    try:
        if stop_event.is_set():
            print("Остановлено до начала работы")
            return

        # Очистка таблицы
        db.query(Purchase).delete()
        db.commit()
        print("Таблица очищена")

        # Парсинг
        data = get_purchases_selenium(
            fz=parser_settings["fz"],
            max_pages=parser_settings["max_pages"],
            region=parser_settings["region"],
            price_min=parser_settings["price_min"],
            price_max=parser_settings["price_max"],
            date_from=parser_settings["date_from"],
            date_to=parser_settings["date_to"]
        )

        print(f"Получено {len(data)} записей")

        # Фильтр категории
        cat = parser_settings.get("category")
        if cat:
            before = len(data)
            data = [d for d in data if filter_by_category(d, cat)]
            print(f"Фильтр '{cat}': {before} → {len(data)}")

        # Сохранение
        for item in data:
            if stop_event.is_set():
                print("Остановлено во время сохранения")
                return

            saved = create_purchase(db, item)
            print(f"Сохранено: {saved.id}")

        print("=== Парсинг завершён успешно ===")

    finally:
        db.close()
        stop_event.clear()
        print("Парсер: ресурсы освобождены")


def start_background_parser():
    """Запуск в отдельном потоке."""
    global parser_thread

    if parser_thread and parser_thread.is_alive():
        return False

    stop_event.clear()
    parser_thread = Thread(target=run_parser_once, daemon=True)
    parser_thread.start()
    return True
