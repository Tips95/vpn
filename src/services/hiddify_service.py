"""Сервис работы с 3x-ui API"""
import httpx
import logging
import time
import json
import uuid
import base64
from typing import Optional, Dict
from urllib.parse import quote

logger = logging.getLogger(__name__)


class HiddifyService:
    """Сервис для работы с 3x-ui VPN панелью"""
    
    def __init__(self, api_url: str, api_token: str, server_host: str, data_limit_gb: int = 100):
        self.api_url = api_url.rstrip('/')
        self.server_host = server_host  # Внешний IP или домен для subscription URL
        self.username = "admin"  # По умолчанию для 3x-ui
        self.password = api_token  # Используем api_token как пароль
        self.data_limit_gb = data_limit_gb
        self.session_cookie = None
        
    async def _login(self) -> bool:
        """Авторизация в 3x-ui панели"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/login",
                    data={
                        "username": self.username,
                        "password": self.password
                    },
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    # Сохраняем все cookies
                    self.session_cookie = "; ".join([f"{k}={v}" for k, v in response.cookies.items()])
                    if self.session_cookie:
                        logger.info("Успешная авторизация в 3x-ui")
                        return True
                    else:
                        # Проверяем ответ
                        try:
                            data = response.json()
                            if data.get("success"):
                                logger.info("Успешная авторизация в 3x-ui (по ответу)")
                                return True
                        except:
                            pass
                        logger.error("Не получены cookies после авторизации")
                        return False
                else:
                    logger.error(f"Ошибка авторизации в 3x-ui: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка при авторизации в 3x-ui: {e}")
            return False
            
    async def create_user(self, expire_days: int) -> Optional[Dict[str, str]]:
        """
        Создать VPN-пользователя в X-UI
        
        Args:
            expire_days: Срок действия подписки в днях
            
        Returns:
            {"uuid": "...", "subscription_url": "..."}
        """
        try:
            # Авторизуемся, если еще не авторизованы
            if not self.session_cookie:
                if not await self._login():
                    return None
            
            # Сначала получим список inbound'ов
            headers = {
                "Cookie": self.session_cookie,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Получаем список inbound'ов
                inbound_response = await client.get(
                    f"{self.api_url}/panel/api/inbounds/list",
                    headers=headers
                )
                
                if inbound_response.status_code != 200:
                    logger.error(f"Не удалось получить список inbound'ов: {inbound_response.status_code}")
                    return None
                
                inbounds_data = inbound_response.json()
                if not inbounds_data.get("success") or not inbounds_data.get("obj"):
                    logger.error("Нет созданных inbound'ов в 3x-ui. Создайте inbound через веб-интерфейс!")
                    return None
                
                # Используем первый доступный inbound
                inbound_id = inbounds_data["obj"][0]["id"]
                logger.info(f"Используем inbound ID: {inbound_id}")
                
                # Генерируем UUID и email для клиента
                client_uuid = str(uuid.uuid4())
                user_email = f"user_{int(time.time())}@vpn.local"
                
                # Красивое название для отображения в приложении
                display_name = "🇳🇱 AI VPN | Netherlands"
                
                # Вычисляем дату истечения (timestamp в миллисекундах)
                expire_time = int((time.time() + (expire_days * 86400)) * 1000)
                
                # Лимит трафика в байтах
                total_gb = self.data_limit_gb * 1024 * 1024 * 1024
                
                # Определяем flow в зависимости от security
                inbound = inbounds_data["obj"][0]
                stream_settings = inbound.get("streamSettings", "{}")
                if isinstance(stream_settings, str):
                    stream_settings = json.loads(stream_settings)
                
                security = stream_settings.get("security", "none")
                flow = "xtls-rprx-vision" if security == "reality" else ""
                
                # Payload для 3x-ui API (settings должен быть JSON-строкой!)
                settings_json = json.dumps({
                    "clients": [{
                        "id": client_uuid,
                        "flow": flow,
                        "email": user_email,
                        "limitIp": 0,
                        "totalGB": total_gb,
                        "expiryTime": expire_time,
                        "enable": True,
                        "tgId": "",
                        "subId": "",
                        "comment": "",
                        "reset": 0
                    }]
                })
                
                client_data = {
                    "id": inbound_id,  # Числовой ID inbound
                    "settings": settings_json  # JSON-строка, не объект!
                }
                
                # Добавляем клиента
                response = await client.post(
                    f"{self.api_url}/panel/api/inbounds/addClient",
                    json=client_data,  # Используем JSON
                    headers={
                        "Cookie": self.session_cookie,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        # Получаем данные inbound для формирования VLESS-ссылки
                        inbound = inbounds_data["obj"][0]
                        port = inbound.get("port", 443)
                        remark = inbound.get("remark", "VPN")
                        
                        # Парсим streamSettings для определения типа security
                        stream_settings = inbound.get("streamSettings", "{}")
                        if isinstance(stream_settings, str):
                            stream_settings = json.loads(stream_settings)
                        
                        network = stream_settings.get("network", "tcp")
                        security = stream_settings.get("security", "none")
                        
                        # Базовые параметры
                        params = {
                            "type": network,
                            "encryption": "none"
                        }
                        
                        # Добавляем параметры в зависимости от типа security
                        if security == "reality":
                            reality_settings = stream_settings.get("realitySettings", {})
                            logger.info(f"Reality settings: {reality_settings}")
                            params["security"] = "reality"
                            
                            # Public Key (обязательно!)
                            pbk = reality_settings.get("publicKey", "")
                            if not pbk:
                                # Пытаемся получить из других возможных полей
                                pbk = reality_settings.get("settings", {}).get("publicKey", "")
                            
                            if pbk:
                                params["pbk"] = pbk
                            else:
                                logger.warning("Public Key не найден в настройках Reality!")
                            
                            params["fp"] = reality_settings.get("fingerprint", "chrome")
                            
                            # SNI из serverNames (берём первый)
                            server_names = reality_settings.get("serverNames", [])
                            if isinstance(server_names, str):
                                server_names = [server_names]
                            if server_names:
                                params["sni"] = server_names[0]
                            
                            # Short IDs (берём первый)
                            short_ids = reality_settings.get("shortIds", [])
                            if isinstance(short_ids, str):
                                short_ids = [short_ids]
                            if short_ids:
                                params["sid"] = short_ids[0]
                            
                            # Flow для Reality (обязательно!)
                            params["flow"] = "xtls-rprx-vision"
                            
                        elif security == "tls":
                            params["security"] = "tls"
                            tls_settings = stream_settings.get("tlsSettings", {})
                            server_names = tls_settings.get("serverName", "")
                            if server_names:
                                params["sni"] = server_names
                            params["fp"] = "chrome"
                        else:
                            params["security"] = "none"
                        
                        # Формируем query string
                        query_parts = [f"{k}={quote(str(v))}" for k, v in params.items() if v]
                        query_string = "&".join(query_parts)
                        
                        # Формируем VLESS-ссылку с красивым названием
                        vless_link = f"vless://{client_uuid}@{self.server_host}:{port}?{query_string}#{quote(display_name)}"
                        
                        logger.info(f"VPN пользователь создан: {user_email} (UUID: {client_uuid})")
                        logger.info(f"Security: {security}, Network: {network}")
                        logger.info(f"VLESS: {vless_link}")
                        
                        return {
                            "uuid": client_uuid,
                            "subscription_url": vless_link,
                            "vless_link": vless_link
                        }
                    else:
                        logger.error(f"3x-ui вернул ошибку: {data.get('msg')}")
                        return None
                else:
                    logger.error(f"Ошибка создания VPN: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.RequestError as e:
            logger.error(f"Ошибка подключения к X-UI API: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании VPN: {e}")
            return None
    
    async def disable_user(self, uuid: str) -> bool:
        """
        Деактивировать VPN-пользователя
        
        Args:
            uuid: Email пользователя в X-UI
            
        Returns:
            True если успешно
        """
        try:
            if not self.session_cookie:
                if not await self._login():
                    return False
            
            headers = {
                "Cookie": f"session={self.session_cookie}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "id": 1,
                "settings": {
                    "clients": [{
                        "email": uuid,
                        "enable": False  # Отключаем пользователя
                    }]
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/xui/inbound/updateClient/{uuid}",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        logger.info(f"VPN пользователь деактивирован: {uuid}")
                        return True
                    else:
                        logger.error(f"Ошибка деактивации: {data.get('msg')}")
                        return False
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
            uuid: Email пользователя в X-UI
            
        Returns:
            Информация о пользователе
        """
        try:
            if not self.session_cookie:
                if not await self._login():
                    return None
            
            headers = {
                "Cookie": f"session={self.session_cookie}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/xui/inbound/list",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        # Ищем клиента по email в списке inbound'ов
                        for inbound in data.get("obj", []):
                            settings = inbound.get("settings", {})
                            clients = settings.get("clients", [])
                            for client in clients:
                                if client.get("email") == uuid:
                                    return client
                        logger.warning(f"Пользователь {uuid} не найден")
                        return None
                    else:
                        logger.error(f"X-UI вернул ошибку: {data.get('msg')}")
                        return None
                else:
                    logger.error(f"Ошибка получения инфо VPN: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при получении инфо VPN: {e}")
            return None
