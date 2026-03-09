"""Клавиатуры для Telegram-бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tariffs_keyboard(show_trial: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура с тарифами"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка пробного периода (если доступна)
    if show_trial:
        builder.row(
            InlineKeyboardButton(
                text="🎁 Получить 7 дней бесплатно",
                callback_data="get_trial"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🌟 1 месяц - 299₽",
            callback_data="tariff:1m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💎 3 месяца - 799₽ (выгодно!)",
            callback_data="tariff:3m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👑 1 год - 2499₽ (самая выгодная!)",
            callback_data="tariff:12m"
        )
    )
    
    # Разделитель
    builder.row(
        InlineKeyboardButton(
            text="📦 Моя подписка",
            callback_data="my_subscription"
        )
    )
    
    # Кнопки внизу (две в ряд)
    builder.row(
        InlineKeyboardButton(
            text="👥 Пригласить друга",
            callback_data="invite_friend"
        ),
        InlineKeyboardButton(
            text="💬 Поддержка",
            url="https://t.me/tipss94"
        )
    )
    
    return builder.as_markup()


def get_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой оплаты"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💳 Оплатить",
            url=payment_url
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tariffs"
        )
    )
    
    return builder.as_markup()


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к тарифам",
            callback_data="back_to_tariffs"
        )
    )
    
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура администратора"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="admin_stats"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 Все пользователи",
            callback_data="admin_users"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📝 Активные подписки",
            callback_data="admin_subscriptions"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🎁 Получить тестовый VPN",
            callback_data="admin_test_vpn"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к тарифам",
            callback_data="back_to_tariffs"
        )
    )
    
    return builder.as_markup()
