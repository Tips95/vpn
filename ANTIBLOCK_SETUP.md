# 🛡️ Настройка Inbound для обхода глушилок (Антиглушилка)

## Шаг 1: Создать самоподписанный сертификат

```bash
# Подключитесь к серверу
ssh root@72.56.102.177

# Создайте сертификат
openssl req -x509 -newkey rsa:4096 -keyout /root/private.key -out /root/cert.crt -days 3650 -nodes -subj "/CN=www.microsoft.com"

# Установите права
chmod 600 /root/private.key
chmod 644 /root/cert.crt
```

---

## Шаг 2: Создать Inbound в 3x-ui

### Откройте панель:
`http://72.56.102.177:2053` (логин: admin, пароль: admin)

### Перейдите в "Inbounds" → "+ Add Inbound"

---

### ⚙️ **General Settings:**

```
Remark: VPN-AntiBlock
Protocol: vless
Listen IP: (оставить пустым)
Port: 8443
Total Flow (GB): 0 (unlimited)
Client Limit: 0 (unlimited)
Expiry Time: оставить пустым
```

---

### 🔐 **Security Settings:**

```
✅ Enable TLS
Certificate File Path: /root/cert.crt
Key File Path: /root/private.key
```

---

### 🌐 **Network Settings:**

```
Network: ws (WebSocket)
```

**WebSocket Settings:**
```
Path: /vpnws
Host: www.microsoft.com
```

---

### 🛡️ **Sniffing Settings:**

```
✅ Enable Sniffing
Destination Override: http,tls,quic,fakedns
```

---

### 🔥 **ВАЖНО: Fragment (обход DPI)**

В поле **"Stream Settings"** (если есть опция Fragment) или в **Advanced Settings**:

Добавить:
```json
{
  "sockopt": {
    "tcpFastOpen": true,
    "tcpMptcp": true,
    "mark": 255
  }
}
```

---

## Шаг 3: Открыть порт 8443

```bash
# На сервере
ufw allow 8443/tcp
ufw status
```

---

## Шаг 4: Проверка

После создания inbound, проверьте:
- Inbound ID должен быть **2**
- Порт **8443** открыт
- TLS включен

---

## 🎉 Готово!

Теперь бот будет генерировать:
- **Обычные ключи** (inbound 1, порт 443, Reality) - быстро
- **Антиглушилка ключи** (inbound 2, порт 8443, WS+TLS) - стабильно при блокировках
