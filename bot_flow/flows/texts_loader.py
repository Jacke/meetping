"""
Loader for bot texts from NocoDB.

This module provides functionality to load bot text strings from NocoDB table pwt37o18yvtfeh6.
"""
import os
import httpx
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_file_path)

NOCODB_API_URL = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
TEXTS_TABLE_ID = "mguawvnumqrb5k7"

# Default texts (fallback if NocoDB is not available)
DEFAULT_TEXTS = {
    "welcome_message": "👋 Добро пожаловать, {user.first_name}!\n\n🎉 Это бот для регистрации и оплаты билетов на наше мероприятие.\n\nНажмите на кнопку ниже, чтобы начать процесс оплаты.",
    "pay_button": "💳 Оплатить билет на мероприятие",
    "payment_info": "💰 <b>Информация для оплаты:</b>\n\n📱 Номер телефона: <code>{PAYMENT_PHONE}</code>\n💵 Сумма: <b>{PAYMENT_AMOUNT}</b>\n\n📋 <b>Инструкция:</b>\n1. Переведите указанную сумму на номер телефона\n2. Дождитесь подтверждения оплаты\n3. После подтверждения вы получите доступ к группе мероприятия\n\n⏳ Ожидаем подтверждения оплаты...",
    "success_message": "✅ <b>Оплата подтверждена!</b>\n\n🎊 Поздравляем! Ваш билет успешно оплачен.\n\n👥 Присоединяйтесь к нашей группе:\n{TELEGRAM_GROUP_LINK}\n\nДо встречи на мероприятии! 🎉"
}


async def load_texts_from_nocodb() -> Dict[str, str]:
    """
    Load all text strings from NocoDB table pwt37o18yvtfeh6.

    Table schema:
        - action (string): text ID/key
        - text (string): text content

    Returns:
        Dict mapping action -> text
    """
    if not NOCODB_API_TOKEN:
        print("⚠️ NocoDB not configured, using default texts")
        return DEFAULT_TEXTS.copy()

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{TEXTS_TABLE_ID}/records",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # Parse records into dict
            texts = {}
            records = data.get("list", []) or data.get("records", [])

            for record in records:
                action = record.get("action")
                text = record.get("text")
                if action and text:
                    texts[action] = text

            print(f"✅ Loaded {len(texts)} texts from NocoDB")
            return texts

    except Exception as e:
        print(f"❌ Error loading texts from NocoDB: {e}")
        print("⚠️ Using default texts as fallback")
        return DEFAULT_TEXTS.copy()


def load_texts_sync() -> Dict[str, str]:
    """Synchronous wrapper for load_texts_from_nocodb (for non-async contexts)"""
    import asyncio
    return asyncio.run(load_texts_from_nocodb())
