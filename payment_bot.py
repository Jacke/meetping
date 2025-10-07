#!/usr/bin/env python3
"""
Telegram bot для оплаты билетов на мероприятие с интеграцией NocoDB
"""
import os
import asyncio
import httpx
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Загрузка переменных окружения
env_file_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_file_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOCODB_API_URL = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = os.getenv("NOCODB_TABLE_ID")

# Настройки оплаты
PAYMENT_PHONE = os.getenv("PAYMENT_PHONE", "+7 (999) 123-45-67")
PAYMENT_AMOUNT = os.getenv("PAYMENT_AMOUNT", "1000 рублей")
TELEGRAM_GROUP_LINK = os.getenv("TELEGRAM_GROUP_LINK", "https://t.me/your_group_link")

# Словарь для отслеживания пользователей, ожидающих оплату
pending_payments: Dict[int, str] = {}  # user_id -> nocodb_record_id


async def create_payment_record(user_id: int, username: str, first_name: str) -> Optional[str]:
    """Создает запись о платеже в NocoDB и возвращает ID записи"""
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB не настроен, используется локальный режим")
        return None

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "TG": username or "",
        "TG ID": user_id,
        "Price": int(PAYMENT_AMOUNT.split()[0]) if PAYMENT_AMOUNT else 1000,
        "Paid": False
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=data,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            return str(result.get("Id") or result.get("id"))
    except Exception as e:
        print(f"❌ Ошибка создания записи в NocoDB: {e}")
        return None


async def check_payment_in_nocodb(record_id: str) -> bool:
    """Проверяет статус оплаты в NocoDB по ID записи"""
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID or not record_id:
        return False

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("Paid", False) is True
    except Exception as e:
        print(f"❌ Ошибка проверки статуса в NocoDB: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user

    keyboard = [
        [InlineKeyboardButton("💳 Оплатить билет на мероприятие", callback_data="pay_ticket")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = (
        f"👋 Добро пожаловать, {user.first_name}!\n\n"
        "🎉 Это бот для регистрации и оплаты билетов на наше мероприятие.\n\n"
        "Нажмите на кнопку ниже, чтобы начать процесс оплаты."
    )

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def payment_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатия на кнопку оплаты"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    # Создаем запись в NocoDB
    record_id = await create_payment_record(user_id, user.username, user.first_name)

    if record_id:
        pending_payments[user_id] = record_id
        print(f"✅ Создана запись в NocoDB: {record_id} для пользователя {user_id}")
    else:
        pending_payments[user_id] = ""
        print(f"⚠️ Локальный режим для пользователя {user_id}")

    payment_message = (
        "💰 <b>Информация для оплаты:</b>\n\n"
        f"📱 Номер телефона: <code>{PAYMENT_PHONE}</code>\n"
        f"💵 Сумма: <b>{PAYMENT_AMOUNT}</b>\n\n"
        "📋 <b>Инструкция:</b>\n"
        "1. Переведите указанную сумму на номер телефона\n"
        "2. Дождитесь подтверждения оплаты\n"
        "3. После подтверждения вы получите доступ к группе мероприятия\n\n"
        "⏳ Ожидаем подтверждения оплаты..."
    )

    await query.edit_message_text(payment_message, parse_mode="HTML")

    # Запускаем проверку статуса оплаты
    asyncio.create_task(check_payment_status(context, user_id, query.message.chat_id))


async def check_payment_status(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> None:
    """Проверка статуса оплаты пользователя в NocoDB"""
    while user_id in pending_payments:
        await asyncio.sleep(10)  # Проверяем каждые 10 секунд

        record_id = pending_payments.get(user_id)
        if not record_id:
            continue

        # Проверяем статус в NocoDB
        is_paid = await check_payment_in_nocodb(record_id)

        if is_paid:
            success_message = (
                "✅ <b>Оплата подтверждена!</b>\n\n"
                f"🎊 Поздравляем! Ваш билет успешно оплачен.\n\n"
                f"👥 Присоединяйтесь к нашей группе:\n"
                f"{TELEGRAM_GROUP_LINK}\n\n"
                "До встречи на мероприятии! 🎉"
            )

            await context.bot.send_message(chat_id=chat_id, text=success_message, parse_mode="HTML")
            del pending_payments[user_id]
            print(f"✅ Оплата подтверждена для пользователя {user_id}")
            break


async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда для ручного подтверждения оплаты (только для разработки/тестирования)
    Использование: /confirm <user_id>
    """
    if not context.args:
        await update.message.reply_text("Использование: /confirm <user_id>")
        return

    try:
        user_id = int(context.args[0])
        if user_id in pending_payments:
            # В production режиме эта команда должна быть отключена
            await update.message.reply_text(
                f"⚠️ Для подтверждения оплаты используйте NocoDB: {NOCODB_API_URL}\n"
                f"User ID: {user_id}\n"
                f"Record ID: {pending_payments[user_id]}"
            )
        else:
            await update.message.reply_text(f"❌ Пользователь {user_id} не ожидает оплаты.")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат user_id")


async def list_pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Список пользователей, ожидающих оплату"""
    if not pending_payments:
        await update.message.reply_text("📋 Нет пользователей, ожидающих оплату.")
        return

    message = "📋 <b>Пользователи, ожидающие оплату:</b>\n\n"
    for user_id, record_id in pending_payments.items():
        message += f"User ID: <code>{user_id}</code> | Record: <code>{record_id or 'local'}</code>\n"

    await update.message.reply_text(message, parse_mode="HTML")


def main() -> None:
    """Запуск бота"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в .env файле!")
        return

    # Проверка конфигурации NocoDB
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB не настроен. Работаем в локальном режиме.")
        print("   Добавьте NOCODB_API_TOKEN и NOCODB_TABLE_ID в .env для полной функциональности")

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("confirm", confirm_payment))
    application.add_handler(CommandHandler("pending", list_pending))
    application.add_handler(CallbackQueryHandler(payment_button, pattern="^pay_ticket$"))

    print("🤖 Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
