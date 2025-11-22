from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, StreamingResponse, PlainTextResponse
from io import BytesIO
import pandas as pd
from sqlalchemy import text
from datetime import datetime

from app.deps import engine
from app.parser_logic import (
    start_background_parser,
    stop_event,
    parser_settings,
    CATEGORY_KEYWORDS
)


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def control_panel():
    return """
    <html><body>
    <h2>Панель управления</h2>
    <button onclick="location.href='/start'">Старт</button>
    <button onclick="location.href='/stop'">Стоп</button>
    <button onclick="location.href='/settings'">Настройки</button>
    <button onclick="location.href='/export'">Экспорт</button>
    </body></html>
    """


@router.get("/start")
def start_parser():
    ok = start_background_parser()
    return {"status": "запущен" if ok else "уже работает"}


@router.get("/stop")
def stop_parser():
    stop_event.set()
    return {"status": "стоп отправлен"}


@router.get("/export")
def export_excel():
    try:
        df = pd.read_sql(text("SELECT * FROM purchases"), con=engine)

        # Переименовываем колонки для Excel
        rename_map = {
            "id": "id",
            "number": "номер заказа",
            "customer": "заказчик",
            "subject": "название заказа",
            "amount": "цена",
            "dates": "даты",
            "status": "тип заказа",
            "link": "ссылка"
        }

        df = df.rename(columns=rename_map)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Закупки")

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="zakupki.xlsx"'}
        )

    except Exception as e:
        return PlainTextResponse(str(e), status_code=500)


@router.get("/settings", response_class=HTMLResponse)
def settings_page():
    # Генерируем <option> для категорий
    category_options = ""
    for cat in CATEGORY_KEYWORDS.keys():
        selected = "selected" if parser_settings.get("category") == cat else ""
        category_options += f"<option value='{cat}' {selected}>{cat.title()}</option>"

    return f"""
    <html><body>
    <h2>Настройки</h2>
    <form action="settings/save" method="post">
        <label>Закон:</label>
        <input name="fz" value="{parser_settings['fz']}"><br><br>

        <label>Регион:</label>
        <input name="region" value="{parser_settings['region'] or ''}"><br><br>

        <label>Цена от:</label>
        <input name="price_min" value="{parser_settings['price_min'] or ''}"><br><br>

        <label>Цена до:</label>
        <input name="price_max" value="{parser_settings['price_max'] or ''}"><br><br>

        <label>Макс страниц:</label>
        <input name="max_pages" value="{parser_settings['max_pages']}"><br><br>

        <label>Категория:</label>
        <select name="category">
            <option value="">(не выбрано)</option>
            {category_options}
        </select>
        <br><br>

        <button>Сохранить</button>
    </form>
    </body></html>
    """


@router.post("/settings/save")
def save_settings(
    fz: str = Form(...),
    region: str = Form(None),
    price_min: str = Form(None),
    price_max: str = Form(None),
    max_pages: int = Form(3),
    category: str = Form(None)
):
    parser_settings["fz"] = fz
    parser_settings["region"] = region or None
    parser_settings["price_min"] = int(price_min) if price_min else None
    parser_settings["price_max"] = int(price_max) if price_max else None
    parser_settings["max_pages"] = max_pages
    parser_settings["category"] = category or None

    return HTMLResponse("<h3>Сохранено!</h3><a href='/'>Назад</a>")
