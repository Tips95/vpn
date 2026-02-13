"""Сервис работы с Hiddify API"""
import httpx
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class HiddifyService:
    """Сервис для работы с Hiddify VPN API"""
    
    def __init__(self, api_url: str, api_token: str, data_limit_gb: int = 100):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.data_limit_gb = data_limit_gb
        
    async def create_user(self, expire_days: int) -> Optional[Dict[str, str]]:
        """
        Создать VPN-пользователя в Hiddify
        
        Args:
            expire_days: Срок действия подписки в днях
            
        Returns:
            {"uuid": "...", "subscription_url": "..."}
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "expire_days": expire_days,
                "data_limit_gb": self.data_limit_gb
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/user",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"VPN пользователь создан: {data.get('uuid')}")
                    return {
                        "uuid": data.get("uuid"),
                        "subscription_url": data.get("subscription_url")
                    }
                else:
                    logger.error(f"Ошибка создания VPN: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Ошибка подключения к Hiddify API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании VPN: {e}")
            return None
    
    async def disable_user(self, uuid: str) -> bool:
        """
        Деактивировать VPN-пользователя
        
        Args:
            uuid: UUID пользователя в Hiddify
            
        Returns:
            True если успешно
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.api_url}/api/user/{uuid}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    logger.info(f"VPN пользователь деактивирован: {uuid}")
                    return True
                else:
                    logger.error(f"Ошибка деактивации VPN: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при деактивации VPN: {e}")
            return False
    
    async def get_user_info(self, uuid: str) -> Optional[Dict]:
        """
        Получить информацию о VPN-пользователе
        
        Args:
            uuid: UUID пользователя в Hiddify
            
        Returns:
            Информация о пользователе
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_url}/api/user/{uuid}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ошибка получения инфо VPN: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении инфо VPN: {e}")
            return None
