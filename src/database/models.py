"""Модели базы данных SQLite"""
import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path


class Database:
    """Менеджер базы данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    trial_used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица подписок
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tariff TEXT NOT NULL,
                    hiddify_uuid TEXT NOT NULL,
                    subscription_url TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Таблица платежей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL,
                    yookassa_payment_id TEXT UNIQUE NOT NULL,
                    amount INTEGER NOT NULL,
                    tariff TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для оптимизации
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id 
                ON users(telegram_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id 
                ON subscriptions(user_id)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_payments_telegram_id 
                ON payments(telegram_id)
            """)
            
            await db.commit()
    
    async def create_user(self, telegram_id: int, username: Optional[str] = None) -> int:
        """Создать пользователя или вернуть существующего"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверить, существует ли пользователь
            async with db.execute(
                "SELECT id FROM users WHERE telegram_id = ?", 
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
            
            # Создать нового пользователя
            cursor = await db.execute(
                "INSERT INTO users (telegram_id, username) VALUES (?, ?)",
                (telegram_id, username)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def create_payment(
        self, 
        telegram_id: int, 
        yookassa_payment_id: str,
        amount: int,
        tariff: str
    ) -> int:
        """Создать запись о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO payments (telegram_id, yookassa_payment_id, amount, tariff, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (telegram_id, yookassa_payment_id, amount, tariff))
            await db.commit()
            return cursor.lastrowid
    
    async def update_payment_status(self, yookassa_payment_id: str, status: str):
        """Обновить статус платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE payments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE yookassa_payment_id = ?
            """, (status, yookassa_payment_id))
            await db.commit()
    
    async def get_payment(self, yookassa_payment_id: str) -> Optional[dict]:
        """Получить информацию о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM payments WHERE yookassa_payment_id = ?",
                (yookassa_payment_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def create_subscription(
        self,
        user_id: int,
        tariff: str,
        hiddify_uuid: str,
        subscription_url: str,
        days: int
    ) -> int:
        """Создать подписку"""
        expires_at = datetime.now() + timedelta(days=days)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Деактивировать старые подписки
            await db.execute("""
                UPDATE subscriptions 
                SET is_active = 0 
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            # Создать новую подписку
            cursor = await db.execute("""
                INSERT INTO subscriptions 
                (user_id, tariff, hiddify_uuid, subscription_url, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, tariff, hiddify_uuid, subscription_url, expires_at))
            
            await db.commit()
            return cursor.lastrowid
    
    async def get_active_subscription(self, telegram_id: int) -> Optional[dict]:
        """Получить активную подписку пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT s.* 
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE u.telegram_id = ? 
                AND s.is_active = 1
                AND s.expires_at > CURRENT_TIMESTAMP
                ORDER BY s.created_at DESC
                LIMIT 1
            """, (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[dict]:
        """Получить пользователя по telegram_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def has_used_trial(self, telegram_id: int) -> bool:
        """Проверить, использовал ли пользователь пробный период"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT trial_used FROM users WHERE telegram_id = ?",
                (telegram_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False
    
    async def mark_trial_used(self, telegram_id: int):
        """Отметить, что пользователь использовал пробный период"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET trial_used = 1 WHERE telegram_id = ?",
                (telegram_id,)
            )
            await db.commit()
    
    async def has_any_subscription(self, telegram_id: int) -> bool:
        """Проверить, были ли у пользователя подписки (включая истекшие)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) 
                FROM subscriptions s
                JOIN users u ON s.user_id = u.id
                WHERE u.telegram_id = ?
            """, (telegram_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] > 0 if row else False
