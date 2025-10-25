"""
Loader for bot configuration from NocoDB.

This module provides functionality to load bot config values from NocoDB table mguawvnumqrb5k7.
"""
import httpx
from typing import Dict
from config import config
from bot_flow.flows.nocodb_utils import nocodb_request_with_retry

# NocoDB configuration from centralized config
NOCODB_API_URL = config.NOCODB_API_URL
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
CONFIG_TABLE_ID = config.NOCODB_CONFIG_TABLE_ID

# Required config keys that MUST be present in NocoDB
REQUIRED_CONFIG_KEYS = [
    "PAYMENT_PHONE",
    "PAYMENT_AMOUNT",
    "TELEGRAM_GROUP_LINK"
]


def validate_config(config_data: Dict[str, str]) -> None:
    """
    Validate that all required config keys are present.

    Raises:
        ValueError: If any required keys are missing
    """
    missing_keys = [key for key in REQUIRED_CONFIG_KEYS if key not in config_data]

    if missing_keys:
        raise ValueError(
            f"❌ Missing required config constants in NocoDB:\n"
            f"   {', '.join(missing_keys)}\n\n"
            f"Please add these config entries to NocoDB table (action column):\n"
            f"   Table URL: {NOCODB_API_URL}/#/nc/{CONFIG_TABLE_ID}\n"
        )


async def load_config_from_nocodb() -> Dict[str, str]:
    """
    Load all config values from NocoDB table mguawvnumqrb5k7.

    Validates that all required config keys are present.
    Bot will not start if any required config values are missing.

    Table schema:
        - action (string): config key (UPPERCASE)
        - text (string): config value

    Returns:
        Dict mapping action -> text

    Raises:
        ValueError: If required config values are missing or NocoDB is not configured
    """
    if not NOCODB_API_TOKEN or not CONFIG_TABLE_ID:
        raise ValueError(
            "❌ NocoDB not configured!\n"
            "   Please set NOCODB_API_TOKEN and NOCODB_CONFIG_TABLE_ID in .env file"
        )

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        response = await nocodb_request_with_retry(
            "GET",
            f"{NOCODB_API_URL}/api/v2/tables/{CONFIG_TABLE_ID}/records",
            headers=headers,
            timeout=15.0
        )
        response.raise_for_status()
        data = response.json()

        # Parse records into dict
        config_data = {}
        records = data.get("list", []) or data.get("records", [])

        for record in records:
            action = record.get("action")
            text = record.get("text")
            if action and text:
                config_data[action] = text

        print(f"✅ Loaded {len(config_data)} config values from NocoDB")

        # Validate all required keys are present
        validate_config(config_data)
        print(f"✅ All required config constants validated")

        return config_data

    except httpx.HTTPError as e:
        raise ValueError(
            f"❌ Error loading config from NocoDB: {e}\n"
            f"   Please check your NOCODB_API_TOKEN and NOCODB_CONFIG_TABLE_ID"
        ) from e
    except Exception as e:
        raise ValueError(f"❌ Unexpected error loading config: {e}") from e


def load_config_sync() -> Dict[str, str]:
    """Synchronous wrapper for load_config_from_nocodb (for non-async contexts)"""
    import asyncio
    return asyncio.run(load_config_from_nocodb())
