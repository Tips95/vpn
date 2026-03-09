"""Клавиатуры для Telegram-бота"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tariffs_keyboard(show_trial: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора режима VPN"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка пробного периода (если доступна)
    if show_trial:
        builder.row(
            InlineKeyboardButton(
                text="🎁 Получить 7 дней бесплатно",
                callback_data="get_trial"
            )
        )
    
    # Выбор режима VPN
    builder.row(
        InlineKeyboardButton(
            text="⚡️ Обычный VPN",
            callback_data="select_mode:normal"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🛡️ Обход глушилок",
            callback_data="select_mode:antiblock"
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


def get_normal_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с обычными тарифами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="⚡️ 1 месяц - 299₽",
            callback_data="tariff:1m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚡️ 3 месяца - 799₽",
            callback_data="tariff:3m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚡️ 1 год - 2499₽",
            callback_data="tariff:12m"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tariffs"
        )
    )
    
    return builder.as_markup()


def get_antiblock_tariffs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с антиглушилка тарифами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🛡️ 1 месяц - 499₽",
            callback_data="tariff:antiblock_1m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🛡️ 3 месяца - 1299₽",
            callback_data="tariff:antiblock_3m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🛡️ 1 год - 3999₽",
            callback_data="tariff:antiblock_12m"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Что такое обход глушилок?",
            callback_data="antiblock_info"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_tariffs"
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
