"""Direct test of NocoDB API"""
import asyncio
import httpx
from config import config


async def test_nocodb():
    print("=" * 60)
    print("Testing NocoDB API Connection")
    print("=" * 60)

    print(f"\n📋 Configuration:")
    print(f"   API URL: {config.NOCODB_API_URL}")
    print(f"   API Token: {config.NOCODB_API_TOKEN[:20]}..." if config.NOCODB_API_TOKEN else "   API Token: Not set")
    print(f"   Texts Table ID: {config.NOCODB_TEXTS_TABLE_ID}")
    print(f"   Config Table ID: {config.NOCODB_CONFIG_TABLE_ID}")
    print(f"   Payments Table ID: {config.NOCODB_TABLE_ID}")

    if not config.NOCODB_API_TOKEN:
        print("\n❌ NOCODB_API_TOKEN not set in .env!")
        return

    headers = {
        "xc-token": config.NOCODB_API_TOKEN
    }

    # Test texts/config table
    print(f"\n1️⃣ Testing table: {config.NOCODB_TEXTS_TABLE_ID}")
    print("-" * 60)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.NOCODB_API_URL}/api/v2/tables/{config.NOCODB_TEXTS_TABLE_ID}/records",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            records = data.get("list", [])

            print(f"✅ Success! Found {len(records)} records")

            # Separate texts and config
            texts = {}
            configs = {}

            for record in records:
                action = record.get("action")
                text = record.get("text")

                # Config keys are in uppercase (PAYMENT_PHONE, etc.)
                if action and text:
                    if action.isupper() or action.startswith("PAYMENT") or action.startswith("TELEGRAM"):
                        configs[action] = text
                    else:
                        texts[action] = text

            print(f"\n📝 Texts ({len(texts)}):")
            for key, value in texts.items():
                preview = value[:60].replace("\n", " ") + "..." if len(value) > 60 else value.replace("\n", " ")
                print(f"   - {key}: {preview}")

            print(f"\n⚙️ Config ({len(configs)}):")
            for key, value in configs.items():
                print(f"   - {key}: {value}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test payments table
    print(f"\n2️⃣ Testing table: {config.NOCODB_TABLE_ID}")
    print("-" * 60)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.NOCODB_API_URL}/api/v2/tables/{config.NOCODB_TABLE_ID}/records",
                headers=headers,
                params={"limit": 3},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            records = data.get("list", [])

            print(f"✅ Success! Found {data.get('pageInfo', {}).get('totalRows', '?')} total records")
            print(f"\nShowing first {len(records)} records:")
            for record in records:
                print(f"   - ID: {record.get('Id')}, TG ID: {record.get('TG ID')}, "
                      f"TG: @{record.get('TG')}, Paid: {record.get('Paid')}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_nocodb())
