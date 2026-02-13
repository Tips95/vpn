"""Скрипт для тестирования YooKassa API"""
import sys
from pathlib import Path

# Добавить корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.services.payment_service import PaymentService


def test_yookassa():
    """Тестирование подключения к YooKassa"""
    print("🔍 Тестирование YooKassa API...")
    print(f"Shop ID: {settings.yookassa_shop_id}")
    
    service = PaymentService(
        settings.yookassa_shop_id,
        settings.yookassa_secret_key
    )
    
    # Создать тестовый платёж
    print("\n📝 Создание тестового платежа (100 RUB)...")
    result = service.create_payment(
        amount=10000,  # 100 RUB в копейках
        telegram_id=123456789,
        tariff_id="1m",
        tariff_name="Тест"
    )
    
    if result:
        print("✅ Платёж создан успешно!")
        print(f"Payment ID: {result['payment_id']}")
        print(f"Статус: {result['status']}")
        print(f"URL для оплаты: {result['confirmation_url']}")
        
        # Получить информацию о платеже
        print(f"\n📊 Получение информации о платеже...")
        info = service.get_payment_info(result['payment_id'])
        if info:
            print("✅ Информация получена:")
            print(f"  ID: {info['id']}")
            print(f"  Статус: {info['status']}")
            print(f"  Сумма: {info['amount'] / 100} RUB")
            print(f"  Оплачен: {info['paid']}")
        else:
            print("❌ Не удалось получить информацию")
            
    else:
        print("❌ Ошибка создания платежа")
        print("Проверьте:")
        print("  1. Shop ID корректен")
        print("  2. Secret Key правильный")
        print("  3. Аккаунт активен в YooKassa")


if __name__ == "__main__":
    try:
        test_yookassa()
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
