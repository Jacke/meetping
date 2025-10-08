"""
Loader for bot configuration from NocoDB.

This module provides functionality to load bot config values from NocoDB table mguawvnumqrb5k7.
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
CONFIG_TABLE_ID = "mguawvnumqrb5k7"

# Default config (fallback if NocoDB is not available)
DEFAULT_CONFIG = {
    "PAYMENT_PHONE": "+7 (999) 123-45-67",
    "PAYMENT_AMOUNT": "1000 рублей",
    "TELEGRAM_GROUP_LINK": "https://t.me/your_group_link"
}


async def load_config_from_nocodb() -> Dict[str, str]:
    """
    Load all config values from NocoDB table mguawvnumqrb5k7.

    Table schema:
        - action (string): config key
        - msg (string): config value

    Returns:
        Dict mapping action -> msg
    """
    if not NOCODB_API_TOKEN:
        print("⚠️ NocoDB not configured, using default config")
        return DEFAULT_CONFIG.copy()

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{CONFIG_TABLE_ID}/records",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # Parse records into dict
            config = {}
            records = data.get("list", []) or data.get("records", [])

            for record in records:
                action = record.get("action")
                msg = record.get("msg")
                if action and msg:
                    config[action] = msg

            print(f"✅ Loaded {len(config)} config values from NocoDB")
            return config

    except Exception as e:
        print(f"❌ Error loading config from NocoDB: {e}")
        print("⚠️ Using default config as fallback")
        return DEFAULT_CONFIG.copy()


def load_config_sync() -> Dict[str, str]:
    """Synchronous wrapper for load_config_from_nocodb (for non-async contexts)"""
    import asyncio
    return asyncio.run(load_config_from_nocodb())
