"""FastAPI приложение"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.database.models import Database
from src.api.webhook import router as webhook_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    # Startup
    logger.info("Инициализация базы данных...")
    db = Database(settings.database_path)
    await db.init_db()
    logger.info("База данных инициализирована")
    
    yield
    
    # Shutdown
    logger.info("Остановка приложения...")


# Создание FastAPI приложения
app = FastAPI(
    title="VPN Bot API",
    description="API для обработки платежей VPN-бота",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(webhook_router, tags=["Webhooks"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "VPN Bot API",
        "version": "1.0.0",
        "status": "running"
    }
