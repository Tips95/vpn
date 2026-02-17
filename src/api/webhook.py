"""API endpoint для webhook от YooKassa"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from src.config.settings import settings
from src.database.models import Database
from src.services.hiddify_service import HiddifyService
from src.services.payment_service import PaymentService
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Инициализация сервисов
db = Database(settings.database_path)
hiddify_service = HiddifyService(
    settings.hiddify_api_url,
    settings.hiddify_api_token,
    settings.server_host,
    settings.vpn_data_limit_gb
)
payment_service = PaymentService(settings.yookassa_shop_id, settings.yookassa_secret_key)
notification_service = NotificationService(settings.telegram_bot_token)


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Webhook для обработки платежей от YooKassa
    
    Вызывается при изменении статуса платежа
    """
    try:
        # Получить данные webhook
        webhook_data = await request.json()
        logger.info(f"Получен webhook от YooKassa: {webhook_data.get('event', 'unknown')}")
        
        # Проверить тип события
        event_type = webhook_data.get("event")
        if event_type != "payment.succeeded":
            logger.info(f"Игнорируем событие {event_type}")
            return {"status": "ok"}
        
        # Извлечь данные платежа
        payment_obj = webhook_data.get("object", {})
        payment_id = payment_obj.get("id")
        payment_status = payment_obj.get("status")
        metadata = payment_obj.get("metadata", {})
        
        if not payment_id:
            raise HTTPException(status_code=400, detail="Missing payment_id")
        
        # Получить telegram_id и tariff_id из metadata
        telegram_id = metadata.get("telegram_id")
        tariff_id = metadata.get("tariff_id")
        
        if not telegram_id or not tariff_id:
            logger.error(f"Отсутствуют telegram_id или tariff_id в metadata: {metadata}")
            raise HTTPException(status_code=400, detail="Missing metadata")
        
        telegram_id = int(telegram_id)
        
        # Проверить, не обработан ли уже этот платёж
        existing_payment = await db.get_payment(payment_id)
        if existing_payment and existing_payment["status"] == "succeeded":
            logger.info(f"Платёж {payment_id} уже обработан")
            return {"status": "ok", "message": "Already processed"}
        
        # Обновить статус платежа в БД
        await db.update_payment_status(payment_id, payment_status)
        
        if payment_status == "succeeded":
            # Получить информацию о тарифе
            tariff_info = settings.get_tariff_info(tariff_id)
            if not tariff_info:
                logger.error(f"Неизвестный тариф: {tariff_id}")
                raise HTTPException(status_code=400, detail="Invalid tariff")
            
            # Создать VPN-пользователя в Hiddify
            vpn_result = await hiddify_service.create_user(tariff_info["days"])
            
            if not vpn_result:
                logger.error(f"Ошибка создания VPN для платежа {payment_id}")
                await notification_service.send_message(
                    telegram_id,
                    "❌ Ошибка создания VPN. Обратитесь в поддержку с ID платежа: " + payment_id
                )
                raise HTTPException(status_code=500, detail="Failed to create VPN")
            
            # Создать пользователя в БД (если не существует)
            user_id = await db.create_user(telegram_id)
            
            # Создать подписку в БД
            await db.create_subscription(
                user_id=user_id,
                tariff=tariff_id,
                hiddify_uuid=vpn_result["uuid"],
                subscription_url=vpn_result["subscription_url"],
                days=tariff_info["days"]
            )
            
            # Рассчитать дату окончания
            expires_at = datetime.now() + timedelta(days=tariff_info["days"])
            
            # Отправить VPN-ключ пользователю
            success = await notification_service.send_vpn_subscription(
                chat_id=telegram_id,
                subscription_url=vpn_result["subscription_url"],
                tariff_name=tariff_info["name"],
                expires_at=expires_at.strftime("%d.%m.%Y %H:%M")
            )
            
            if success:
                logger.info(f"VPN-ключ отправлен пользователю {telegram_id}")
            else:
                logger.error(f"Не удалось отправить VPN-ключ пользователю {telegram_id}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "vpn-bot-api",
        "timestamp": datetime.now().isoformat()
    }
