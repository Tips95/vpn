"""Конфигурация приложения"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    
    # YooKassa
    yookassa_shop_id: str = Field(..., env="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str = Field(..., env="YOOKASSA_SECRET_KEY")
    
    # 3x-ui API
    hiddify_api_url: str = Field(default="http://127.0.0.1:2053", env="HIDDIFY_API_URL")
    hiddify_api_token: str = Field(..., env="HIDDIFY_API_TOKEN")  # Пароль от 3x-ui панели
    
    # Server
    server_host: str = Field(..., env="SERVER_HOST")  # Внешний IP или домен сервера (для subscription URL)
    webhook_url: str = Field(..., env="WEBHOOK_URL")
    webhook_secret: str = Field(..., env="WEBHOOK_SECRET")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    
    # Database
    database_path: str = Field(default="./data/vpn_bot.db", env="DATABASE_PATH")
    
    # Tariffs (prices in RUB kopeks)
    tariff_1m_price: int = Field(default=29900, env="TARIFF_1M_PRICE")  # 299 RUB
    tariff_3m_price: int = Field(default=79900, env="TARIFF_3M_PRICE")  # 799 RUB
    tariff_12m_price: int = Field(default=249900, env="TARIFF_12M_PRICE")  # 2499 RUB
    
    # VPN limits
    vpn_data_limit_gb: int = Field(default=100, env="VPN_DATA_LIMIT_GB")
    
    # Trial period
    trial_period_days: int = Field(default=7, env="TRIAL_PERIOD_DAYS")
    trial_enabled: bool = Field(default=True, env="TRIAL_ENABLED")
    
    # Admin users (telegram IDs separated by comma)
    admin_users: str = Field(default="", env="ADMIN_USERS")
    
    @validator("database_path")
    def create_db_directory(cls, v):
        """Создать директорию для базы данных"""
        db_path = Path(v)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("tariff_1m_price", "tariff_3m_price", "tariff_12m_price")
    def validate_prices(cls, v):
        """Проверка корректности цен"""
        if v <= 0:
            raise ValueError("Цена должна быть положительной")
        return v
    
    def get_tariff_info(self, tariff_id: str) -> dict:
        """Получить информацию о тарифе"""
        tariffs = {
            "1m": {
                "name": "1 месяц",
                "days": 30,
                "price": self.tariff_1m_price,
                "price_rub": self.tariff_1m_price / 100
            },
            "3m": {
                "name": "3 месяца",
                "days": 90,
                "price": self.tariff_3m_price,
                "price_rub": self.tariff_3m_price / 100
            },
            "12m": {
                "name": "1 год",
                "days": 365,
                "price": self.tariff_12m_price,
                "price_rub": self.tariff_12m_price / 100
            }
        }
        return tariffs.get(tariff_id)
    
    def is_admin(self, telegram_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        if not self.admin_users:
            return False
        admin_ids = [int(id.strip()) for id in self.admin_users.split(',') if id.strip()]
        return telegram_id in admin_ids
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр настроек
settings = Settings()
