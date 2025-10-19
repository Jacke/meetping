"""
Script to upload bot config to NocoDB table mguawvnumqrb5k7.

Usage:
    python upload_config_to_nocodb.py
"""
import asyncio
import httpx
from config import config

# NocoDB configuration from centralized config
NOCODB_API_URL = config.NOCODB_API_URL
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
CONFIG_TABLE_ID = config.NOCODB_CONFIG_TABLE_ID

# Config entries to upload (default values)
CONFIG = {
    "PAYMENT_PHONE": "+7 (999) 123-45-67",
    "PAYMENT_AMOUNT": "1000 рублей",
    "TELEGRAM_GROUP_LINK": "https://t.me/your_group_link"
}


async def upload_config():
    """Upload all config values to NocoDB table"""
    if not NOCODB_API_TOKEN:
        print("❌ NOCODB_API_TOKEN not found in .env file!")
        return

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"📤 Uploading {len(CONFIG)} config values to NocoDB table {CONFIG_TABLE_ID}...")

    async with httpx.AsyncClient() as client:
        for action, msg in CONFIG.items():
            data = {
                "action": action,
                "text": msg
            }

            try:
                response = await client.post(
                    f"{NOCODB_API_URL}/api/v2/tables/{CONFIG_TABLE_ID}/records",
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                record_id = result.get("Id") or result.get("id")
                print(f"  ✅ {action}: {msg} (ID: {record_id})")

            except Exception as e:
                print(f"  ❌ {action}: {e}")

    print("\n✨ Upload complete!")


if __name__ == "__main__":
    asyncio.run(upload_config())
