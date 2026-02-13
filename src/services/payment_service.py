"""Сервис работы с платежами YooKassa"""
import uuid
import logging
from yookassa import Configuration, Payment
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class PaymentService:
    """Сервис для работы с YooKassa"""
    
    def __init__(self, shop_id: str, secret_key: str):
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        
    def create_payment(
        self,
        amount: int,
        telegram_id: int,
        tariff_id: str,
        tariff_name: str,
        return_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Создать платёж в YooKassa
        
        Args:
            amount: Сумма в копейках
            telegram_id: ID пользователя в Telegram
            tariff_id: Идентификатор тарифа (1m, 3m, 12m)
            tariff_name: Название тарифа для описания
            return_url: URL возврата после оплаты
            
        Returns:
            {"payment_id": "...", "confirmation_url": "..."}
        """
        try:
            idempotence_key = str(uuid.uuid4())
            
            payment_data = {
                "amount": {
                    "value": f"{amount / 100:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or "https://t.me/your_bot"
                },
                "capture": True,
                "description": f"VPN подписка: {tariff_name}",
                "metadata": {
                    "telegram_id": str(telegram_id),
                    "tariff_id": tariff_id
                }
            }
            
            payment = Payment.create(payment_data, idempotence_key)
            
            logger.info(f"Платёж создан: {payment.id} для user {telegram_id}")
            
            return {
                "payment_id": payment.id,
                "confirmation_url": payment.confirmation.confirmation_url,
                "status": payment.status
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания платежа: {e}")
            return None
    
    def get_payment_info(self, payment_id: str) -> Optional[Dict]:
        """
        Получить информацию о платеже
        
        Args:
            payment_id: ID платежа в YooKassa
            
        Returns:
            Информация о платеже
        """
        try:
            payment = Payment.find_one(payment_id)
            
            return {
                "id": payment.id,
                "status": payment.status,
                "amount": int(float(payment.amount.value) * 100),
                "paid": payment.paid,
                "metadata": payment.metadata
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения платежа: {e}")
            return None
    
    def verify_webhook_signature(self, webhook_data: dict) -> bool:
        """
        Проверить подпись webhook от YooKassa
        
        Args:
            webhook_data: Данные webhook
            
        Returns:
            True если подпись валидна
        """
        # YooKassa использует IP whitelist вместо signature
        # Дополнительная проверка через get_payment_info
        try:
            payment_id = webhook_data.get("object", {}).get("id")
            if not payment_id:
                return False
                
            payment_info = self.get_payment_info(payment_id)
            return payment_info is not None
            
        except Exception as e:
            logger.error(f"Ошибка проверки webhook: {e}")
            return False
