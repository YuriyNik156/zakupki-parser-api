from fastapi import FastAPI
from app.api.endpoints import router
from app.models import Base
from app.deps import engine

app = FastAPI(
    title="Zakupki Parser API",
    description="API для получения и сохранения данных о закупках",
)

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# Подключаем эндпоинты
app.include_router(router, prefix="/api")
