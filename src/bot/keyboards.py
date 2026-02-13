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
            text="🌟 1 месяц",
            callback_data="tariff:1m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💎 3 месяца (выгодно!)",
            callback_data="tariff:3m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👑 1 год (самая выгодная!)",
            callback_data="tariff:12m"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Моя подписка",
            callback_data="my_subscription"
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
