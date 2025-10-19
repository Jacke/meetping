"""
Script to add 'already_registered_message' text to NocoDB
"""
import asyncio
import httpx
from config import config


async def add_already_registered_message():
    """Add already_registered_message to NocoDB table"""

    if not config.NOCODB_API_TOKEN or not config.NOCODB_TEXTS_TABLE_ID:
        print("❌ NocoDB not configured!")
        return

    headers = {
        "xc-token": config.NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    # Check if record already exists
    print("🔍 Checking if 'already_registered_message' already exists...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.NOCODB_API_URL}/api/v2/tables/{config.NOCODB_TEXTS_TABLE_ID}/records",
                headers=headers,
                params={
                    "where": "(action,eq,already_registered_message)",
                    "limit": 1
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            if data.get("list"):
                print("✅ Record already exists!")
                record = data["list"][0]
                print(f"   ID: {record.get('Id')}")
                print(f"   Text: {record.get('text')[:100]}...")
                return

    except Exception as e:
        print(f"❌ Error checking existing record: {e}")
        return

    # Add new record
    print("\n➕ Adding new 'already_registered_message' record...")

    new_record = {
        "action": "already_registered_message",
        "text": (
            "✅ <b>Вы уже зарегистрированы на мероприятие!</b>\n\n"
            "🎊 Вы уже оплатили билет и зарегистрировались на наше мероприятие.\n\n"
            "👥 Ссылка на группу мероприятия:\n"
            "{TELEGRAM_GROUP_LINK}\n\n"
            "До встречи на мероприятии! 🎉"
        )
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.NOCODB_API_URL}/api/v2/tables/{config.NOCODB_TEXTS_TABLE_ID}/records",
                headers=headers,
                json=new_record,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()

            print("✅ Successfully added new record!")
            print(f"   ID: {result.get('Id') or result.get('id')}")
            print(f"   Action: {new_record['action']}")
            print(f"   Text: {new_record['text'][:100]}...")

    except Exception as e:
        print(f"❌ Error adding record: {e}")


if __name__ == "__main__":
    asyncio.run(add_already_registered_message())
