"""
Test script for user registration check functionality
"""
import asyncio
import sys
from unittest.mock import MagicMock
from bot_flow.flows.payment_flow import check_user_registration, reload_texts_and_config
from config import config

# Mock FlowContext for testing
class MockFlowContext:
    def __init__(self, user_id, username="testuser"):
        self.user = MagicMock()
        self.user.id = user_id
        self.user.username = username
        self.user.first_name = "Test"
        self.data = {}

    def set(self, key, value):
        self.data[key] = value
        print(f"  Context.set('{key}', {value})")

    def get(self, key, default=None):
        return self.data.get(key, default)


async def test_registration_check():
    """Test the registration check with different user IDs"""

    print("=" * 60)
    print("Testing User Registration Check")
    print("=" * 60)

    if not config.NOCODB_API_TOKEN or not config.NOCODB_TABLE_ID:
        print("❌ NocoDB not configured!")
        print("   Set NOCODB_API_TOKEN and NOCODB_TABLE_ID in .env")
        return

    print(f"\n✅ NocoDB configured:")
    print(f"   API URL: {config.NOCODB_API_URL}")
    print(f"   Table ID: {config.NOCODB_TABLE_ID}")

    # Test with a non-existent user
    print("\n" + "-" * 60)
    print("Test 1: Non-existent user (ID: 999999999)")
    print("-" * 60)
    ctx1 = MockFlowContext(user_id=999999999, username="nonexistent")
    result1 = await check_user_registration(ctx1)
    print(f"\n  Result: already_registered = {result1}")
    print(f"  Expected: False (new user)")

    # Test with a user ID that exists (you'll need to provide a real ID from your DB)
    if len(sys.argv) > 1:
        existing_user_id = int(sys.argv[1])
        print("\n" + "-" * 60)
        print(f"Test 2: Existing user (ID: {existing_user_id})")
        print("-" * 60)
        ctx2 = MockFlowContext(user_id=existing_user_id, username="existing_user")
        result2 = await check_user_registration(ctx2)
        print(f"\n  Result: already_registered = {result2}")
        print(f"  Expected: True (existing user)")
        print(f"  Record ID: {ctx2.get('record_id')}")
        print(f"  Payment confirmed: {ctx2.get('payment_confirmed')}")
    else:
        print("\n" + "-" * 60)
        print("Test 2: Skipped")
        print("-" * 60)
        print("  To test with existing user ID, run:")
        print(f"  python3 {sys.argv[0]} <user_id>")

    # Test reload texts
    print("\n" + "-" * 60)
    print("Test 3: Reload texts and config")
    print("-" * 60)
    ctx3 = MockFlowContext(user_id=123456, username="test")
    await reload_texts_and_config(ctx3)
    print(f"\n  Texts loaded: {len(ctx3.get('texts', {}))} entries")
    print(f"  Config loaded: {len(ctx3.get('config', {}))} entries")

    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_registration_check())
