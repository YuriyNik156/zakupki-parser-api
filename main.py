from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from threading import Thread, Event

from app.api.endpoints import router
from app.models import Base
from app.deps import engine

print("<<< MAIN.PY STARTED >>>")

# -----------------------------------------------------
# ЕДИНСТВЕННЫЙ APP
# -----------------------------------------------------
app = FastAPI(
    title="Zakupki Parser API",
    description="API для получения и сохранения данных о закупках",
)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

print(">>> IMPORT router:", router)

# Подключаем API маршруты
app.include_router(router, prefix="/api")


# -----------------------------------------------------
# ЛОГИКА СТАРТ/СТОП
# -----------------------------------------------------
stop_event = Event()
parser_thread = None


def run_parser():
    from app.parser.gos_zakupki_parser import get_purchases_selenium
    from app.deps import get_db
    from app.crud import create_purchase
    db = next(get_db())  # получаем сессию SQLAlchemy вручную
    while not stop_event.is_set():
        try:
            data = get_purchases_selenium()
            print(f"Получено {len(data)} записей")
            for item in data:
                saved = create_purchase(db, item)
                print(f"Сохранена запись: {saved.id}")
        except Exception as e:
            print("Ошибка в парсере:", e)


# -----------------------------------------------------
# ГЛАВНАЯ СТРАНИЦА (ИНТЕРФЕЙС)
# -----------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def control_panel():
    return """
    <html>
    <head>
        <title>Панель управления</title>
        <style>
            body { 
                font-family: Arial; 
                margin: 40px; 
            }
            button {
                width: 200px;
                padding: 15px;
                margin: 10px;
                font-size: 18px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h2>Панель управления парсером</h2>
        <button onclick="location.href='/start'">Старт</button>
        <button onclick="location.href='/stop'">Стоп</button>
        <button onclick="alert('Настройки пока не реализованы')">Настройки</button>
        <button onclick="alert('Экспорт пока не реализован')">Экспорт</button>
    </body>
    </html>
    """


@app.get("/start")
def start_parser():
    global parser_thread

    if parser_thread and parser_thread.is_alive():
        return {"status": "уже работает"}

    stop_event.clear()
    parser_thread = Thread(target=run_parser, daemon=True)
    parser_thread.start()

    return {"status": "парсер запущен"}


@app.get("/stop")
def stop_parser():
    stop_event.set()
    return {"status": "парсер остановлен"}
