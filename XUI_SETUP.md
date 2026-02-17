# Настройка X-UI панели

## Доступ к панели

После установки X-UI доступна по адресу:
- **URL**: `http://ВАШ_IP:54321`
- **Логин по умолчанию**: `admin`
- **Пароль по умолчанию**: `admin`

⚠️ **ВАЖНО**: Сразу после первого входа смените логин и пароль!

## Первоначальная настройка

### 1. Вход в панель

Откройте в браузере `http://ВАШ_IP:54321` и войдите с дефолтными учетными данными.

### 2. Смена пароля

1. Перейдите в **Settings** → **Panel Settings**
2. Измените **Username** и **Password**
3. Сохраните новые учетные данные в `.env` файл бота:
   ```
   HIDDIFY_API_TOKEN=ВАШ_НОВЫЙ_ПАРОЛЬ
   ```

### 3. Настройка Inbound (обязательно!)

X-UI по умолчанию может не иметь настроенных inbound'ов. Нужно создать один:

#### Создание VLESS Inbound:

1. Перейдите в **Inbounds** → **Add Inbound**
2. Заполните параметры:
   - **Remark**: `VPN-Bot-Users`
   - **Protocol**: `VLESS`
   - **Listen IP**: `0.0.0.0`
   - **Port**: `443` (или любой свободный)
   - **Network**: `tcp` или `ws` (рекомендуется `tcp`)
   - **Security**: `reality` или `tls` (для продакшена)
3. В разделе **Settings**:
   - Включите **Enable**
   - Отметьте **Enable Stats**
4. Нажмите **Create**

**Важно**: Запомните **ID** созданного inbound (обычно `1` для первого). Этот ID используется в коде бота.

### 4. Настройка подписок (subscription)

1. Перейдите в **Settings** → **Subscription**
2. Включите **Enable Subscription**
3. Укажите **Subscription URL**: `http://ВАШ_IP:54321` или ваш домен
4. Сохраните

### 5. Настройка SSL (опционально, для продакшена)

Для продакшена рекомендуется использовать SSL:

```bash
# Установка Certbot
apt install certbot -y

# Получение сертификата
certbot certonly --standalone -d ваш-домен.com

# Настройка в X-UI
# В панели: Settings → SSL Certificate
# Certificate Path: /etc/letsencrypt/live/ваш-домен.com/fullchain.pem
# Private Key Path: /etc/letsencrypt/live/ваш-домен.com/privkey.pem
```

## Проверка работы

### Тест через API

```bash
# Получение списка inbound'ов
curl -X POST http://ВАШ_IP:54321/login \
  -d "username=admin&password=admin"

# Сохраните полученную cookie сессии
curl -X POST http://ВАШ_IP:54321/xui/inbound/list \
  -H "Cookie: session=ВАША_СЕССИЯ"
```

### Тест создания пользователя

Используйте скрипт `scripts/test_hiddify.py` (работает с X-UI):

```bash
python scripts/test_hiddify.py
```

## Обновление конфигурации бота

После настройки X-UI обновите `.env` на сервере:

```bash
cd /opt/vpn-bot
nano .env
```

Убедитесь, что указаны:
```
HIDDIFY_API_URL=http://127.0.0.1:54321
HIDDIFY_API_TOKEN=ВАШ_НОВЫЙ_ПАРОЛЬ
```

Перезапустите бота:
```bash
systemctl restart vpn-bot
```

## Мониторинг

### Проверка статуса контейнера X-UI:
```bash
docker ps | grep xui
docker logs xui
```

### Проверка логов бота:
```bash
journalctl -u vpn-bot -f
```

## Troubleshooting

### Панель не открывается
- Проверьте, запущен ли контейнер: `docker ps | grep xui`
- Проверьте firewall: `ufw allow 54321/tcp`

### Не создаются пользователи
- Убедитесь, что создан хотя бы один inbound
- Проверьте правильность ID inbound в коде (по умолчанию `1`)
- Проверьте, что в `.env` указан правильный пароль

### Ошибки авторизации
- Проверьте логин и пароль в панели
- Обновите `HIDDIFY_API_TOKEN` в `.env`
