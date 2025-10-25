"""
Loader for bot texts from NocoDB.

This module provides functionality to load bot text strings from NocoDB table pwt37o18yvtfeh6.
"""
import httpx
from typing import Dict
from config import config
from bot_flow.flows.nocodb_utils import nocodb_request_with_retry

# NocoDB configuration from centralized config
NOCODB_API_URL = config.NOCODB_API_URL
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
TEXTS_TABLE_ID = config.NOCODB_TEXTS_TABLE_ID

# Required text keys that MUST be present in NocoDB
REQUIRED_TEXT_KEYS = [
    "welcome_message",
    "pay_button",
    "payment_info",
    "success_message",
    "already_registered_message"
]


def validate_texts(texts: Dict[str, str]) -> None:
    """
    Validate that all required text keys are present.

    Raises:
        ValueError: If any required keys are missing
    """
    missing_keys = [key for key in REQUIRED_TEXT_KEYS if key not in texts]

    if missing_keys:
        raise ValueError(
            f"❌ Missing required text constants in NocoDB:\n"
            f"   {', '.join(missing_keys)}\n\n"
            f"Please add these text entries to NocoDB table (action column):\n"
            f"   Table URL: {NOCODB_API_URL}/#/nc/{TEXTS_TABLE_ID}\n"
        )


async def load_texts_from_nocodb() -> Dict[str, str]:
    """
    Load all text strings from NocoDB table pwt37o18yvtfeh6.

    Validates that all required text keys are present.
    Bot will not start if any required texts are missing.

    Table schema:
        - action (string): text ID/key (lowercase)
        - text (string): text content

    Returns:
        Dict mapping action -> text

    Raises:
        ValueError: If required texts are missing or NocoDB is not configured
    """
    if not NOCODB_API_TOKEN or not TEXTS_TABLE_ID:
        raise ValueError(
            "❌ NocoDB not configured!\n"
            "   Please set NOCODB_API_TOKEN and NOCODB_TEXTS_TABLE_ID in .env file"
        )

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        response = await nocodb_request_with_retry(
            "GET",
            f"{NOCODB_API_URL}/api/v2/tables/{TEXTS_TABLE_ID}/records",
            headers=headers,
            timeout=15.0
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

        # Validate all required keys are present
        validate_texts(texts)
        print(f"✅ All required text constants validated")

        return texts

    except httpx.HTTPError as e:
        raise ValueError(
            f"❌ Error loading texts from NocoDB: {e}\n"
            f"   Please check your NOCODB_API_TOKEN and NOCODB_TEXTS_TABLE_ID"
        ) from e
    except Exception as e:
        raise ValueError(f"❌ Unexpected error loading texts: {e}") from e


def load_texts_sync() -> Dict[str, str]:
    """Synchronous wrapper for load_texts_from_nocodb (for non-async contexts)"""
    import asyncio
    return asyncio.run(load_texts_from_nocodb())
