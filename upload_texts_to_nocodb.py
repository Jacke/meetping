"""
Script to upload bot texts to NocoDB table pwt37o18yvtfeh6.

Usage:
    python upload_texts_to_nocodb.py
"""
import asyncio
import httpx
from config import config

# NocoDB configuration from centralized config
NOCODB_API_URL = config.NOCODB_API_URL
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
TEXTS_TABLE_ID = config.NOCODB_TEXTS_TABLE_ID

# Text entries to upload
TEXTS = {
    "welcome_message": (
        "👋 Добро пожаловать, {user.first_name}!\n\n"
        "🎉 Это бот для регистрации и оплаты билетов на наше мероприятие.\n\n"
        "Нажмите на кнопку ниже, чтобы начать процесс оплаты."
    ),
    "pay_button": "💳 Оплатить билет на мероприятие",
    "payment_info": (
        "💰 <b>Информация для оплаты:</b>\n\n"
        "📱 Номер телефона: <code>{PAYMENT_PHONE}</code>\n"
        "💵 Сумма: <b>{PAYMENT_AMOUNT}</b>\n\n"
        "📋 <b>Инструкция:</b>\n"
        "1. Переведите указанную сумму на номер телефона\n"
        "2. Дождитесь подтверждения оплаты\n"
        "3. После подтверждения вы получите доступ к группе мероприятия\n\n"
        "⏳ Ожидаем подтверждения оплаты..."
    ),
    "success_message": (
        "✅ <b>Оплата подтверждена!</b>\n\n"
        "🎊 Поздравляем! Ваш билет успешно оплачен.\n\n"
        "👥 Присоединяйтесь к нашей группе:\n"
        "{TELEGRAM_GROUP_LINK}\n\n"
        "До встречи на мероприятии! 🎉"
    )
}


async def upload_texts():
    """Upload all texts to NocoDB table"""
    if not NOCODB_API_TOKEN:
        print("❌ NOCODB_API_TOKEN not found in .env file!")
        return

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"📤 Uploading {len(TEXTS)} texts to NocoDB table {TEXTS_TABLE_ID}...")

    async with httpx.AsyncClient() as client:
        for action, text in TEXTS.items():
            data = {
                "action": action,
                "text": text
            }

            try:
                response = await client.post(
                    f"{NOCODB_API_URL}/api/v2/tables/{TEXTS_TABLE_ID}/records",
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                record_id = result.get("Id") or result.get("id")
                print(f"  ✅ {action}: {record_id}")

            except Exception as e:
                print(f"  ❌ {action}: {e}")

    print("\n✨ Upload complete!")


if __name__ == "__main__":
    asyncio.run(upload_texts())
