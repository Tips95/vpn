"""Скрипт для тестирования Hiddify API"""
import asyncio
import sys
from pathlib import Path

# Добавить корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.services.hiddify_service import HiddifyService


async def test_hiddify():
    """Тестирование подключения к Hiddify"""
    print("🔍 Тестирование Hiddify API...")
    print(f"URL: {settings.hiddify_api_url}")
    
    service = HiddifyService(
        settings.hiddify_api_url,
        settings.hiddify_api_token,
        settings.vpn_data_limit_gb
    )
    
    # Создать тестового пользователя
    print("\n📝 Создание тестового VPN-пользователя (30 дней)...")
    result = await service.create_user(expire_days=30)
    
    if result:
        print("✅ Успешно!")
        print(f"UUID: {result['uuid']}")
        print(f"Subscription URL: {result['subscription_url']}")
        
        # Получить информацию о пользователе
        print(f"\n📊 Получение информации о пользователе...")
        info = await service.get_user_info(result['uuid'])
        if info:
            print("✅ Информация получена:")
            print(info)
        else:
            print("❌ Не удалось получить информацию")
            
    else:
        print("❌ Ошибка создания VPN-пользователя")
        print("Проверьте:")
        print("  1. Hiddify запущен и доступен")
        print("  2. API токен корректен")
        print("  3. URL правильный")


if __name__ == "__main__":
    try:
        asyncio.run(test_hiddify())
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
