"""Сервис отправки уведомлений в Telegram"""
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки сообщений через Telegram Bot API"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Отправить сообщение пользователю
        
        Args:
            chat_id: ID чата в Telegram
            text: Текст сообщения
            parse_mode: Режим парсинга (HTML, Markdown)
            disable_web_page_preview: Отключить превью ссылок
            
        Returns:
            True если успешно отправлено
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_web_page_preview
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Сообщение отправлено пользователю {chat_id}")
                    return True
                else:
                    logger.error(f"Ошибка отправки сообщения: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False
    
    async def send_vpn_subscription(
        self,
        chat_id: int,
        subscription_url: str,
        tariff_name: str,
        expires_at: str
    ) -> bool:
        """
        Отправить VPN-подписку пользователю
        
        Args:
            chat_id: ID чата в Telegram
            subscription_url: URL подписки
            tariff_name: Название тарифа
            expires_at: Дата окончания подписки
            
        Returns:
            True если успешно отправлено
        """
        message = f"""
✅ <b>Оплата успешно получена!</b>

🔑 <b>Ваш VPN-ключ:</b>
<code>{subscription_url}</code>

📦 <b>Тариф:</b> {tariff_name}
📅 <b>Действителен до:</b> {expires_at}

<b>📱 Как подключиться:</b>
1. Скачайте приложение:
   • iOS: <a href="https://apps.apple.com/app/v2box/id6446814690">V2Box</a>, <a href="https://apps.apple.com/app/happ-plus/id6738878751">Happ Plus</a>
   • Android: <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">v2rayNG</a>, <a href="https://play.google.com/store/apps/details?id=one.happ.plus">Happ Plus</a>

2. Скопируйте ключ выше
3. Откройте приложение → Добавить конфигурацию → Вставить из буфера

❓ Возникли вопросы? Пишите @tipss94
"""
        
        return await self.send_message(chat_id, message)
    
    async def send_payment_failed(
        self,
        chat_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Уведомить о неудачной оплате
        
        Args:
            chat_id: ID чата в Telegram
            reason: Причина отказа
            
        Returns:
            True если успешно отправлено
        """
        message = f"""
❌ <b>Оплата не прошла</b>

{f'Причина: {reason}' if reason else 'Попробуйте еще раз или выберите другой способ оплаты.'}

Для повторной оплаты используйте команду /start
"""
        
        return await self.send_message(chat_id, message)
