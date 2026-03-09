"""Обработчики команд Telegram-бота"""
import logging
import aiosqlite
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.config.settings import settings
from src.database.models import Database
from src.services.payment_service import PaymentService
from src.services.hiddify_service import HiddifyService
from src.services.notification_service import NotificationService
from src.bot.keyboards import get_tariffs_keyboard, get_payment_keyboard, get_back_keyboard, get_admin_keyboard

logger = logging.getLogger(__name__)

router = Router()
db = Database(settings.database_path)
payment_service = PaymentService(settings.yookassa_shop_id, settings.yookassa_secret_key)
hiddify_service = HiddifyService(
    settings.hiddify_api_url,
    settings.hiddify_api_token,
    settings.server_host,
    settings.vpn_data_limit_gb
)
notification_service = NotificationService(settings.telegram_bot_token)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    # Создать пользователя в БД (если новый)
    await db.create_user(user.id, user.username)
    
    # Получить информацию о подписке
    subscription = await db.get_active_subscription(user.id)
    
    # Формируем имя пользователя
    user_name = user.first_name or user.username or "Пользователь"
    
    # Формируем блок профиля
    profile_text = f"""
🛡️ <b>Добро пожаловать в AI VPN!</b>

👤 <b>Профиль:</b>
• ID: <code>{user.id}</code>
• Имя: {user_name}
"""
    
    # Формируем блок подписки
    if subscription:
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        days_left = (expires_at - datetime.now()).days
        
        if subscription["tariff"] == "trial":
            tariff_name = f"🎁 Пробный период"
        else:
            tariff_info = settings.get_tariff_info(subscription["tariff"])
            tariff_name = tariff_info["name"] if tariff_info else subscription["tariff"]
        
        if days_left > 0:
            subscription_text = f"""
📦 <b>Подписка:</b>
• Тариф: {tariff_name}
• Срок действия до: {expires_at.strftime("%d.%m.%Y")}
• Осталось дней: <b>{days_left}</b>
"""
        else:
            subscription_text = f"""
⚠️ <b>Подписка:</b>
• Срок действия истек: {expires_at.strftime("%d.%m.%Y")}

<i>Ваш бесплатный пробный период закончился. Оформите подписку, чтобы продолжить пользоваться сервисом!</i>
"""
    else:
        # Проверить доступность пробного периода
        has_trial = await db.has_used_trial(user.id)
        
        if not has_trial and settings.trial_enabled:
            subscription_text = f"""
🎁 <b>Пробная подписка:</b>
• Доступно <b>{settings.trial_period_days} дней бесплатно!</b>

<i>Попробуйте наш VPN бесплатно без привязки карты.</i>
"""
        else:
            subscription_text = """
📭 <b>Подписка:</b>
• Срок действия истек.

<i>Выберите тариф для продолжения использования.</i>
"""
    
    welcome_text = profile_text + subscription_text
    
    # Проверить доступность пробного периода для кнопки
    show_trial = False
    if settings.trial_enabled:
        has_trial = await db.has_used_trial(user.id)
        has_subs = await db.has_any_subscription(user.id)
        show_trial = not has_trial and not has_subs
    
    await message.answer(welcome_text, reply_markup=get_tariffs_keyboard(show_trial=show_trial))


@router.callback_query(F.data == "get_trial")
async def process_trial_request(callback: CallbackQuery):
    """Обработчик запроса пробного периода"""
    user = callback.from_user
    
    # Проверить, использовал ли пользователь пробный период
    has_trial = await db.has_used_trial(user.id)
    
    if has_trial:
        # Пробный период уже использован
        await callback.answer()
        await callback.message.edit_text(
            """
❌ <b>Пробный период уже использован</b>

Вы уже получали бесплатный пробный период ранее.

Выберите один из платных тарифов, чтобы продолжить пользоваться VPN.
""",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Выдать пробный период
    await callback.answer()
    await callback.message.edit_text(
        "⏳ <b>Создание пробного доступа...</b>\n\nПодождите несколько секунд."
    )
    
    try:
        # Получить user_id из БД
        user_data = await db.get_user_by_telegram_id(user.id)
        if not user_data:
            await callback.message.edit_text(
                "❌ Ошибка: пользователь не найден в базе данных."
            )
            return
        
        user_id = user_data["id"]
        
        # Создать VPN в Hiddify
        vpn_result = await hiddify_service.create_user(settings.trial_period_days)
        
        if not vpn_result:
            await callback.message.edit_text(
                "❌ <b>Ошибка создания VPN</b>\n\nПопробуйте позже или обратитесь в поддержку."
            )
            return
        
        # Сохранить подписку в БД
        await db.create_subscription(
            user_id=user_id,
            tariff="trial",
            hiddify_uuid=vpn_result["uuid"],
            subscription_url=vpn_result["subscription_url"],
            days=settings.trial_period_days
        )
        
        # Отметить, что пробный период использован
        await db.mark_trial_used(user.id)
        
        # Отправить VPN-ключ
        expires_at = datetime.now() + timedelta(days=settings.trial_period_days)
        trial_text = f"""
🎉 <b>Пробный период активирован!</b>

🎁 <b>Вы получили {settings.trial_period_days} дней бесплатного доступа!</b>

🔑 <b>Ваш VPN-ключ:</b>
<code>{vpn_result["subscription_url"]}</code>

📅 <b>Действует до:</b> {expires_at.strftime("%d.%m.%Y %H:%M")}

<b>📱 Как подключиться:</b>
1. Скачайте приложение:
   • iOS: <a href="https://apps.apple.com/app/v2box/id6446814690">V2Box</a>, <a href="https://apps.apple.com/app/happ-plus/id6738878751">Happ Plus</a>
   • Android: <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">v2rayNG</a>, <a href="https://play.google.com/store/apps/details?id=one.happ.plus">Happ Plus</a>

2. Скопируйте ключ выше (нажмите на него)
3. Откройте приложение → Добавить конфигурацию → Вставить из буфера

После окончания пробного периода вы сможете выбрать платный тариф.

❓ Возникли вопросы? Пишите @tipss94
"""
        
        await callback.message.edit_text(trial_text)
        logger.info(f"Пробный период выдан пользователю {user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка выдачи пробного периода: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка</b>\n\nПопробуйте позже или обратитесь в поддержку."
        )


@router.callback_query(F.data.startswith("tariff:"))
async def process_tariff_selection(callback: CallbackQuery):
    """Обработчик выбора тарифа"""
    tariff_id = callback.data.split(":")[1]
    tariff_info = settings.get_tariff_info(tariff_id)
    
    if not tariff_info:
        await callback.answer("❌ Тариф не найден")
        return
    
    # Создать платёж
    payment_data = payment_service.create_payment(
        amount=tariff_info["price"],
        telegram_id=callback.from_user.id,
        tariff_id=tariff_id,
        tariff_name=tariff_info["name"]
    )
    
    if not payment_data:
        await callback.message.answer("❌ Ошибка создания платежа. Попробуйте позже.")
        return
    
    # Сохранить платёж в БД
    await db.create_payment(
        telegram_id=callback.from_user.id,
        yookassa_payment_id=payment_data["payment_id"],
        amount=tariff_info["price"],
        tariff=tariff_id
    )
    
    payment_text = f"""
💰 <b>Оплата подписки</b>

📦 <b>Тариф:</b> {tariff_info["name"]}
💵 <b>Стоимость:</b> {tariff_info["price_rub"]:.0f} ₽

После успешной оплаты вы автоматически получите VPN-ключ.

<i>Принимаем СБП и карты РФ</i>
"""
    
    await callback.message.edit_text(
        payment_text,
        reply_markup=get_payment_keyboard(payment_data["confirmation_url"])
    )
    await callback.answer()


@router.callback_query(F.data == "my_subscription")
async def show_subscription(callback: CallbackQuery):
    """Показать информацию о подписке"""
    subscription = await db.get_active_subscription(callback.from_user.id)
    
    if not subscription:
        text = """
📭 <b>У вас нет активной подписки</b>

Выберите тариф, чтобы продолжить пользоваться VPN.
"""
    else:
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        days_left = (expires_at - datetime.now()).days
        
        # Определить название тарифа
        if subscription["tariff"] == "trial":
            tariff_name = f"🎁 Пробный период"
        else:
            tariff_info = settings.get_tariff_info(subscription["tariff"])
            tariff_name = tariff_info["name"] if tariff_info else subscription["tariff"]
        
        # Статус подписки
        if days_left > 0:
            status_emoji = "✅"
            status_text = f"Активна | Осталось <b>{days_left} дн.</b>"
        else:
            status_emoji = "⚠️"
            status_text = f"Истекла {expires_at.strftime('%d.%m.%Y')}"
        
        text = f"""
{status_emoji} <b>Ваша подписка</b>

📦 <b>Тариф:</b> {tariff_name}
📅 <b>Статус:</b> {status_text}
📅 <b>Действует до:</b> {expires_at.strftime("%d.%m.%Y")}

🔑 <b>Ваш VPN-ключ:</b>
<code>{subscription["subscription_url"]}</code>

📱 <b>Как подключиться:</b>
1. Скопируйте ключ выше (нажмите на него)
2. Откройте V2Box, Happ Plus или v2rayNG
3. Нажмите "+" → "Вставить из буфера"

❓ Вопросы? Пишите @tipss94
"""
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_tariffs")
async def back_to_tariffs(callback: CallbackQuery):
    """Вернуться к выбору тарифов"""
    user = callback.from_user
    
    # Получить информацию о подписке
    subscription = await db.get_active_subscription(user.id)
    
    # Формируем имя пользователя
    user_name = user.first_name or user.username or "Пользователь"
    
    # Формируем блок профиля
    profile_text = f"""
🛡️ <b>Добро пожаловать в AI VPN!</b>

👤 <b>Профиль:</b>
• ID: <code>{user.id}</code>
• Имя: {user_name}
"""
    
    # Формируем блок подписки
    if subscription:
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        days_left = (expires_at - datetime.now()).days
        
        if subscription["tariff"] == "trial":
            tariff_name = f"🎁 Пробный период"
        else:
            tariff_info = settings.get_tariff_info(subscription["tariff"])
            tariff_name = tariff_info["name"] if tariff_info else subscription["tariff"]
        
        if days_left > 0:
            subscription_text = f"""
📦 <b>Подписка:</b>
• Тариф: {tariff_name}
• Срок действия до: {expires_at.strftime("%d.%m.%Y")}
• Осталось дней: <b>{days_left}</b>
"""
        else:
            subscription_text = f"""
⚠️ <b>Подписка:</b>
• Срок действия истек: {expires_at.strftime("%d.%m.%Y")}

<i>Ваш бесплатный пробный период закончился. Оформите подписку, чтобы продолжить пользоваться сервисом!</i>
"""
    else:
        # Проверить доступность пробного периода
        has_trial = await db.has_used_trial(user.id)
        
        if not has_trial and settings.trial_enabled:
            subscription_text = f"""
🎁 <b>Пробная подписка:</b>
• Доступно <b>{settings.trial_period_days} дней бесплатно!</b>

<i>Попробуйте наш VPN бесплатно без привязки карты.</i>
"""
        else:
            subscription_text = """
📭 <b>Подписка:</b>
• Срок действия истек.

<i>Выберите тариф для продолжения использования.</i>
"""
    
    text = profile_text + subscription_text
    
    # Проверить доступность пробного периода для кнопки
    show_trial = False
    if settings.trial_enabled:
        has_trial = await db.has_used_trial(callback.from_user.id)
        has_subs = await db.has_any_subscription(callback.from_user.id)
        show_trial = not has_trial and not has_subs
    
    await callback.message.edit_text(text, reply_markup=get_tariffs_keyboard(show_trial=show_trial))
    await callback.answer()


@router.callback_query(F.data == "invite_friend")
async def invite_friend(callback: CallbackQuery):
    """Пригласить друга"""
    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=ref_{callback.from_user.id}"
    
    invite_text = f"""
👥 <b>Пригласите друзей!</b>

Поделитесь ссылкой с друзьями:
<code>{invite_link}</code>

<b>Что получит друг:</b>
🎁 {settings.trial_period_days} дней бесплатного VPN
⚡️ Высокая скорость без ограничений
🔒 Полная конфиденциальность

<i>Просто отправьте ссылку, и ваш друг сможет сразу начать пользоваться VPN!</i>
"""
    
    await callback.message.edit_text(invite_text, reply_markup=get_back_keyboard())
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = f"""
<b>📚 Помощь</b>

<b>Команды:</b>
/start - Главное меню
/help - Эта справка

<b>Пробный период:</b>
🎁 Новые пользователи получают {settings.trial_period_days} дней бесплатно!

<b>Как подключиться:</b>
1. Получите VPN-ключ (при первом запуске автоматически)
2. Скачайте приложение:
   • iOS: V2Box, Happ Plus
   • Android: v2rayNG, Happ Plus
3. Добавьте конфигурацию из ключа

<b>Поддержка:</b>
По всем вопросам: @tipss94
"""
    
    await message.answer(help_text)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель (только для администраторов)"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели")
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Показать статистику"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return
    
    # Получить статистику из БД
    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM subscriptions WHERE is_active = 1")
        active_subs = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT COUNT(*) FROM payments WHERE status = 'succeeded'")
        total_payments = (await cursor.fetchone())[0]
        
        cursor = await conn.execute("SELECT SUM(amount) FROM payments WHERE status = 'succeeded'")
        total_revenue = (await cursor.fetchone())[0] or 0
        
        text = (
            "📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{total_users}</b>\n"
            f"📝 Активных подписок: <b>{active_subs}</b>\n"
            f"💰 Успешных платежей: <b>{total_payments}</b>\n"
            f"💵 Общий доход: <b>{total_revenue / 100:.2f} ₽</b>"
        )
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
        await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Показать список пользователей"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute(
            "SELECT telegram_id, created_at FROM users ORDER BY created_at DESC LIMIT 20"
        )
        users = await cursor.fetchall()
        
        text = "👥 <b>Последние 20 пользователей:</b>\n\n"
        for user in users:
            text += f"ID: <code>{user[0]}</code> | {user[1]}\n"
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
        await callback.answer()


@router.callback_query(F.data == "admin_subscriptions")
async def admin_subscriptions(callback: CallbackQuery):
    """Показать активные подписки"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return
    
    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("""
            SELECT s.id, u.telegram_id, s.tariff, s.expires_at, s.hiddify_uuid
            FROM subscriptions s
            JOIN users u ON s.user_id = u.id
            WHERE s.is_active = 1
            ORDER BY s.created_at DESC
            LIMIT 15
        """)
        subs = await cursor.fetchall()
        
        if not subs:
            text = "📝 <b>Нет активных подписок</b>"
        else:
            text = "📝 <b>Активные подписки (последние 15):</b>\n\n"
            for sub in subs:
                tariff_name = sub[2] if sub[2] != "trial" else "Пробный период"
                text += (
                    f"🆔 <code>{sub[1]}</code> | {tariff_name}\n"
                    f"   Истекает: {sub[3]}\n\n"
                )
        
        await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
        await callback.answer()


@router.callback_query(F.data == "admin_test_vpn")
async def admin_test_vpn(callback: CallbackQuery):
    """Создать тестовый VPN для админа"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔️ Доступ запрещен", show_alert=True)
        return
    
    await callback.answer("⏳ Создаю VPN...", show_alert=False)
    
    # Создать VPN на 30 дней
    vpn_data = await hiddify_service.create_user(expire_days=30)
    
    if vpn_data:
        # Получить user_id
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (callback.from_user.id,)
            )
            user = await cursor.fetchone()
            
            if user:
                # Сохранить подписку
                await db.create_subscription(
                    user_id=user[0],
                    tariff="admin_test",
                    hiddify_uuid=vpn_data["uuid"],
                    subscription_url=vpn_data["subscription_url"],
                    days=30
                )
        
        text = (
            "✅ <b>Тестовый VPN создан!</b>\n\n"
            "📅 Срок: 30 дней\n"
            "💾 Трафик: 100 GB\n\n"
            "🔗 <b>Ваш VPN-ключ:</b>\n"
            f"<code>{vpn_data['subscription_url']}</code>\n\n"
            "📱 <b>Как подключиться:</b>\n"
            "1. Скопируйте ссылку выше\n"
            "2. Откройте V2rayNG/V2Box/Happ Plus\n"
            "3. Нажмите '+' → 'Import from clipboard'\n"
            "4. Подключитесь к серверу!\n\n"
            "❓ Вопросы? Пишите @tipss94"
        )
        await callback.message.answer(text, parse_mode="HTML")
        await callback.message.edit_text(
            "🔧 <b>Админ-панель</b>",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.answer("❌ Ошибка создания VPN")
        await callback.answer()


@router.message()
async def echo_handler(message: Message):
    """Обработчик остальных сообщений"""
    user = message.from_user
    
    # Получить информацию о подписке
    subscription = await db.get_active_subscription(user.id)
    
    # Формируем имя пользователя
    user_name = user.first_name or user.username or "Пользователь"
    
    # Формируем блок профиля
    profile_text = f"""
🛡️ <b>AI VPN</b>

👤 <b>Профиль:</b>
• ID: <code>{user.id}</code>
• Имя: {user_name}
"""
    
    # Формируем блок подписки
    if subscription:
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        days_left = (expires_at - datetime.now()).days
        
        if subscription["tariff"] == "trial":
            tariff_name = f"🎁 Пробный период"
        else:
            tariff_info = settings.get_tariff_info(subscription["tariff"])
            tariff_name = tariff_info["name"] if tariff_info else subscription["tariff"]
        
        if days_left > 0:
            subscription_text = f"""
📦 <b>Подписка:</b>
• Тариф: {tariff_name}
• Срок действия до: {expires_at.strftime("%d.%m.%Y")}
• Осталось дней: <b>{days_left}</b>
"""
        else:
            subscription_text = f"""
⚠️ <b>Подписка:</b>
• Срок действия истек: {expires_at.strftime("%d.%m.%Y")}

<i>Выберите тариф для продолжения.</i>
"""
    else:
        # Проверить доступность пробного периода
        has_trial = await db.has_used_trial(user.id)
        
        if not has_trial and settings.trial_enabled:
            subscription_text = f"""
🎁 <b>Пробная подписка:</b>
• Доступно <b>{settings.trial_period_days} дней бесплатно!</b>
"""
        else:
            subscription_text = """
📭 <b>Подписка:</b>
• Срок действия истек.
"""
    
    text = profile_text + subscription_text
    
    # Проверить доступность пробного периода для кнопки
    show_trial = False
    if settings.trial_enabled:
        has_trial = await db.has_used_trial(message.from_user.id)
        has_subs = await db.has_any_subscription(message.from_user.id)
        show_trial = not has_trial and not has_subs
    
    await message.answer(
        text,
        reply_markup=get_tariffs_keyboard(show_trial=show_trial)
    )
