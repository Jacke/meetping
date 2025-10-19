"""Test NocoDB loaders"""
import asyncio
from bot_flow.flows.texts_loader import load_texts_from_nocodb
from bot_flow.flows.config_loader import load_config_from_nocodb


async def main():
    print("=" * 60)
    print("Testing NocoDB Loaders")
    print("=" * 60)

    # Test texts loader
    print("\n1. Loading texts from NocoDB...")
    texts = await load_texts_from_nocodb()
    print(f"\n✅ Loaded {len(texts)} texts:")
    for key, value in texts.items():
        preview = value[:50] + "..." if len(value) > 50 else value
        print(f"   - {key}: {preview}")

    # Test config loader
    print("\n2. Loading config from NocoDB...")
    config = await load_config_from_nocodb()
    print(f"\n✅ Loaded {len(config)} config values:")
    for key, value in config.items():
        print(f"   - {key}: {value}")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
