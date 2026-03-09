# 🛡️ Настройка Reality Inbound для обхода глушилок (Антиглушилка)

## ✅ Текущая конфигурация

Антиглушилка настроена на **Reality protocol** (порт 441) для обхода DPI-блокировок.

### Преимущества Reality:
- 🚀 **Высокая скорость** - работает напрямую через TCP без накладных расходов WebSocket
- 🛡️ **Обход глушилок DPI** - маскируется под легитимный HTTPS-трафик к ads.x5.ru
- 🔒 **Безопасность** - использует протокол XTLS с шифрованием
- 📱 **Совместимость** - работает со всеми клиентами (V2rayNG, V2Box, Happ Plus)

---

## 📋 Конфигурация inbound "VPN-AntiBlock-Reality"

### Основные параметры:
```
Remark: VPN-AntiBlock-Reality
Protocol: vless
Port: 441
Listen IP: (пусто)
Enable: ✅
```

### Stream Settings:
```
Network: tcp
Security: reality

Reality Settings:
├─ Target (Dest): ads.x5.ru:443
├─ SNI (Server Names): ads.x5.ru
├─ uTLS (Fingerprint): chrome
├─ Short IDs: (автогенерация, например: 5041e8,7d38e1...)
├─ Public Key: (автогенерация)
└─ Private Key: (автогенерация)

Flow Settings:
└─ Flow Control: xtls-rprx-vision
```

### Sniffing (для обнаружения типа трафика):
```
✅ Enable Sniffing
Sniffing Types: ✅ HTTP ✅ TLS ✅ QUIC ✅ FAKEDNS
```

---

## 🔧 Если нужно пересоздать inbound:

### 1. Откройте панель 3x-ui:
```
http://72.56.102.177:2053
```

### 2. Inbounds → Add Inbound

### 3. Заполните параметры как указано выше

### 4. Откройте порт в firewall:
```bash
ufw allow 441/tcp
ufw status
```

---

## 🧪 Проверка работы:

### Создать тестовый ключ через бота:
1. `/admin` → "🛡️ Тестовый VPN (антиглушилка)"
2. Скопировать ключ
3. Добавить в приложение (V2Box/Happ Plus)
4. Проверить подключение

### Проверка в логах бота:
```bash
journalctl -u vpn-bot -f | grep ANTIBLOCK
```

Должно быть:
```
✅ ANTIBLOCK Reality inbound: ID=4, Port=441, Remark=VPN-AntiBlock-Reality
```

---

## 📱 Как работает обход глушилок:

Reality маскирует VPN-трафик под обычный HTTPS-запрос к российскому домену **ads.x5.ru** (X5 Retail Group - Пятёрочка, Перекрёсток):

```
🌐 Интернет провайдер видит:
   └─> HTTPS запрос к ads.x5.ru (легитимный трафик) ✅

🔐 На самом деле:
   └─> Зашифрованный VPN-трафик через Reality + XTLS 🚀
```

**Результат:** DPI-глушилки не могут отличить VPN от обычного браузинга! 🎉

---

## ⚠️ Важно:

1. **Не удаляйте** inbound "VPN-AntiBlock-Reality" - он нужен для платных подписок
2. **Порт 441** должен быть открыт в firewall
3. **Target/SNI** должны указывать на **ads.x5.ru** (незаблокированный домен в РФ)
4. **Security** обязательно должен быть **reality** (не TLS, не WebSocket)

---

## 🆘 Проблемы и решения:

### Ключ не работает (timeout):
```bash
# Проверить порт
ufw status | grep 441

# Проверить inbound в 3x-ui
curl -s http://127.0.0.1:2053/panel/api/inbounds/list | jq '.obj[] | select(.remark | contains("AntiBlock"))'

# Перезапустить контейнер
docker restart xui
```

### Бот выбирает неправильный inbound:
```bash
# Убедитесь что remark содержит "antiblock":
VPN-AntiBlock-Reality ✅
VPN AntiBlock Reality ✅
antiblock-reality ✅

vpn-reality ❌ (не содержит "antiblock")
```

---

## 📊 Сравнение режимов:

| Параметр | Обычный VPN | Обход глушилок |
|----------|-------------|----------------|
| Протокол | Reality | Reality |
| Порт | 443 | 441 |
| Target | www.cloudflare.com | ads.x5.ru |
| Обход DPI | Частично | ✅ Полный |
| Скорость | Быстро | Быстро |
| Цена | Обычная | Премиум |

---

**Готово! Антиглушилка настроена и работает! 🔥**
