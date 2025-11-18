from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
from threading import Thread, Event
from io import BytesIO
import pandas as pd
from sqlalchemy import text
from datetime import datetime

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
# ЛОГИКА СТАРТ/СТОП (фоновый поток парсера)
# -----------------------------------------------------
stop_event = Event()
parser_thread = None


# -----------------------------------------------------
# Глобальные настройки парсера (меняются через /settings)
# -----------------------------------------------------
parser_settings = {
    "fz": "44",
    "region": None,
    "price_min": None,
    "price_max": None,
    "date_from": None,
    "date_to": None,
    "max_pages": 3
}


def run_parser():
    from app.parser.gos_zakupki_parser import get_purchases_selenium
    from app.deps import get_db
    from app.crud import create_purchase

    db = next(get_db())  # получаем сессию SQLAlchemy вручную
    try:
        while not stop_event.is_set():
            try:
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
                for item in data:
                    saved = create_purchase(db, item)
                    print(f"Сохранена запись: {saved.id}")
            except Exception as e:
                # Логируем ошибку парсинга, но не убиваем поток
                print("Ошибка в парсере:", repr(e))
    finally:
        try:
            db.close()
        except Exception:
            pass


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
        <button onclick="location.href='/settings'">Настройки</button>
        <button onclick="location.href='/export'">Экспорт</button>
        <p style="color:gray;margin-top:20px">Экспорт сохраняет весь текущий набор данных из таблицы <code>purchases</code> в файл Excel.</p>
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


# -----------------------------------------------------
#   EXPORT: выгружаем данные из БД в Excel и скачиваем
# -----------------------------------------------------
@app.get("/export")
def export_excel():
    try:
        df = pd.read_sql(text("SELECT * FROM purchases"), con=engine)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="purchases")
        output.seek(0)

        headers = {
            "Content-Disposition": 'attachment; filename="zakupki_export.xlsx"'
        }
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except Exception as e:
        print("Ошибка при экспорте в Excel:", repr(e))
        return PlainTextResponse(f"Ошибка при экспорте: {e}", status_code=500)


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return f"""
    <html>
    <body>
        <h2>Настройки парсинга</h2>
        <form method="post" action="/settings/save">

            <label>Закон (44 или 223):</label><br>
            <input name="fz" value="{parser_settings['fz']}"><br><br>

            <label>Регион:</label><br>
            <input name="region" value="{parser_settings['region'] or ''}"><br><br>

            <label>Цена от:</label><br>
            <input name="price_min" value="{parser_settings['price_min'] or ''}"><br><br>

            <label>Цена до:</label><br>
            <input name="price_max" value="{parser_settings['price_max'] or ''}"><br><br>

            <label>Дата с:</label><br>
            <input name="date_from" value="{parser_settings['date_from'] or ''}"><br><br>

            <label>Дата по:</label><br>
            <input name="date_to" value="{parser_settings['date_to'] or ''}"><br><br>

            <label>Максимум страниц:</label><br>
            <input name="max_pages" value="{parser_settings['max_pages']}"><br><br>

            <button type="submit">Сохранить</button>
        </form>

        <br><button onclick="location.href='/'">Назад</button>
    </body>
    </html>
    """

def parse_date(d):
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except:
        return None

@app.post("/settings/save")
def save_settings(
    fz: str = Form(...),
    region: str = Form(None),
    price_min: str = Form(None),
    price_max: str = Form(None),
    date_from: str = Form(None),
    date_to: str = Form(None),
    max_pages: int = Form(3)
):
    parser_settings["fz"] = fz
    parser_settings["region"] = region or None
    parser_settings["price_min"] = int(price_min) if price_min else None
    parser_settings["price_max"] = int(price_max) if price_max else None
    parser_settings["date_from"] = parse_date(date_from)
    parser_settings["date_to"] = parse_date(date_to)
    parser_settings["max_pages"] = max_pages

    return HTMLResponse("""
    <html>
    <head><meta charset="utf-8"></head>
    <body>
        <h3>Настройки сохранены!</h3>
        <button onclick="location.href='/'">Назад</button>
    </body>
    </html>
    """)