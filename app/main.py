from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.ui_routes import router as ui_router
from app.models import Base
from app.deps import engine

app = FastAPI(title="Zakupki Parser API")

# Создаём таблицы
Base.metadata.create_all(bind=engine)

# API
app.include_router(api_router)

# UI
app.include_router(ui_router)
