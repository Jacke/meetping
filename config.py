"""
Centralized configuration module for MeetPing-Pay project.
All environment variables should be loaded here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


class Config:
    """Application configuration"""

    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/bot.log")

    # NocoDB
    NOCODB_API_URL: str = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
    NOCODB_API_TOKEN: Optional[str] = os.getenv("NOCODB_API_TOKEN")
    NOCODB_TABLE_ID: Optional[str] = os.getenv("NOCODB_TABLE_ID")

    # NocoDB Tables (static table IDs)
    # Note: Both texts and config are stored in the same table (mguawvnumqrb5k7)
    NOCODB_TEXTS_TABLE_ID: str = "mguawvnumqrb5k7"
    NOCODB_CONFIG_TABLE_ID: str = "mguawvnumqrb5k7"

    # OpenAI (for agents)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # Environment
    ENV: str = os.getenv("ENV", "dev")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "file:meetping.db?cache=shared&mode=rwc")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            print("❌ BOT_TOKEN is required in .env file!")
            return False
        return True

    @classmethod
    def is_nocodb_configured(cls) -> bool:
        """Check if NocoDB is properly configured"""
        return bool(cls.NOCODB_API_TOKEN and cls.NOCODB_TABLE_ID)

    @classmethod
    def print_status(cls):
        """Print configuration status"""
        print("📋 Configuration Status:")
        print(f"   BOT_TOKEN: {'✅ Set' if cls.BOT_TOKEN else '❌ Missing'}")
        print(f"   NocoDB: {'✅ Configured' if cls.is_nocodb_configured() else '⚠️ Not configured (local mode)'}")
        print(f"   OpenAI: {'✅ Set' if cls.OPENAI_API_KEY else '⚠️ Not set'}")
        print(f"   Environment: {cls.ENV}")


# Export singleton instance
config = Config()
