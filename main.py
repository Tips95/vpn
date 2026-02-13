"""Главная точка входа приложения"""
import asyncio
import logging
from multiprocessing import Process

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from src.config.settings import settings
from src.bot.handlers import router as bot_router
from src.database.models import Database

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def start_bot():
    """Запуск Telegram-бота"""
    logger.info("Запуск Telegram-бота...")
    
    # Инициализация БД
    db = Database(settings.database_path)
    await db.init_db()
    
    # Инициализация бота
    bot = Bot(token=settings.telegram_bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(bot_router)
    
    # Удаление старых webhook'ов
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск бота
    logger.info("Бот запущен и готов к работе")
    await dp.start_polling(bot)


def start_api():
    """Запуск FastAPI сервера"""
    logger.info(f"Запуск API сервера на {settings.api_host}:{settings.api_port}...")
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level="info",
        access_log=True
    )


def main():
    """Главная функция"""
    try:
        # Проверка настроек
        logger.info("Проверка конфигурации...")
        logger.info(f"Database: {settings.database_path}")
        logger.info(f"Webhook URL: {settings.webhook_url}")
        logger.info(f"Hiddify API: {settings.hiddify_api_url}")
        
        # Запуск API в отдельном процессе
        api_process = Process(target=start_api)
        api_process.start()
        
        # Запуск бота в основном процессе
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        api_process.terminate()
        api_process.join()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
