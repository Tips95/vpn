# VPN Bot - Коммерческий VPN-сервис

Telegram-бот для автоматической продажи VPN-подписок с интеграцией YooKassa и X-UI панели.

## Возможности

- ✅ Автоматическая выдача VPN-ключей после оплаты
- ✅ Интеграция с YooKassa (СБП, карты РФ)
- ✅ X-UI панель для управления VPN (VLESS/Reality)
- ✅ 7 дней бесплатного пробного периода для новых пользователей
- ✅ 3 тарифных плана (1, 3, 12 месяцев)
- ✅ SQLite база данных
- ✅ FastAPI backend для обработки webhook'ов

## Стек технологий

- **Backend**: FastAPI + Uvicorn
- **Bot**: aiogram 3.x
- **Database**: SQLite + aiosqlite
- **Payment**: YooKassa API
- **VPN Panel**: X-UI (Docker)
- **Deployment**: systemd + Nginx + Certbot

## Быстрый старт

### Требования

- Python 3.10+
- VPS с Ubuntu 20.04+
- Docker и Docker Compose (для X-UI)
- Домен с SSL сертификатом (для webhook'ов)

### Установка

Полная инструкция по развертыванию находится в [DEPLOY.md](DEPLOY.md)

Краткая версия:

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Tips95/vpn.git /opt/vpn-bot
cd /opt/vpn-bot

# 2. Установить зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Настроить переменные окружения
cp .env.example .env
nano .env

# 4. Установить X-UI панель (см. XUI_SETUP.md)

# 5. Запустить бота
python main.py
```

## Конфигурация

### Переменные окружения (.env)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather

# YooKassa
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key

# X-UI Panel
HIDDIFY_API_URL=http://127.0.0.1:54321
HIDDIFY_API_TOKEN=пароль_от_x-ui

# Server
WEBHOOK_URL=https://ваш-домен.com/webhook/yookassa
WEBHOOK_SECRET=случайная_строка

# Tariffs (prices in kopeks)
TARIFF_1M_PRICE=29900    # 299₽
TARIFF_3M_PRICE=79900    # 799₽
TARIFF_12M_PRICE=249900  # 2499₽

# Trial
TRIAL_ENABLED=True
TRIAL_PERIOD_DAYS=7
```

## Настройка X-UI панели

Подробная инструкция: [XUI_SETUP.md](XUI_SETUP.md)

Кратко:
1. Установите X-UI через Docker Compose
2. Зайдите на `http://ваш_ip:54321`
3. Смените дефолтный пароль (admin/admin)
4. Создайте VLESS inbound
5. Укажите новый пароль в `.env`

## Структура проекта

```
/opt/vpn-bot/
├── main.py                     # Точка входа
├── requirements.txt            # Зависимости
├── .env                        # Конфигурация
├── src/
│   ├── config/
│   │   └── settings.py         # Настройки приложения
│   ├── database/
│   │   └── models.py           # SQLite модели
│   ├── services/
│   │   ├── hiddify_service.py  # X-UI API клиент
│   │   ├── payment_service.py  # YooKassa интеграция
│   │   └── notification_service.py
│   ├── bot/
│   │   ├── handlers.py         # Telegram обработчики
│   │   └── keyboards.py        # Клавиатуры
│   └── api/
│       ├── app.py              # FastAPI приложение
│       └── webhook.py          # YooKassa webhook
└── scripts/
    ├── test_hiddify.py         # Тест X-UI API
    └── test_yookassa.py        # Тест YooKassa
```

## Развертывание на продакшене

См. [DEPLOY.md](DEPLOY.md) для полной инструкции по:
- Настройке systemd сервисов
- Конфигурации Nginx с SSL
- Настройке firewall
- Мониторингу и логам

## Тестирование

### Тест X-UI API
```bash
python scripts/test_hiddify.py
```

### Тест YooKassa
```bash
python scripts/test_yookassa.py
```

### Локальный запуск
```bash
python main.py
```

## Поддержка и помощь

- Telegram: @Tips95
- GitHub Issues: https://github.com/Tips95/vpn/issues

## Лицензия

Проприетарный коммерческий проект
