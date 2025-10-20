#!/usr/bin/env python3
"""
Test script to verify validation of required texts and config constants.
This script simulates missing constants to test validation logic.
"""
import asyncio
import sys
import os

# Add parent directory to path to import modules directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import validation functions directly (without loading telegram dependencies)
import importlib.util

def load_module_from_file(module_name, file_path):
    """Load a Python module from file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

texts_loader = load_module_from_file("texts_loader", "bot_flow/flows/texts_loader.py")
config_loader = load_module_from_file("config_loader", "bot_flow/flows/config_loader.py")

validate_texts = texts_loader.validate_texts
REQUIRED_TEXT_KEYS = texts_loader.REQUIRED_TEXT_KEYS
validate_config = config_loader.validate_config
REQUIRED_CONFIG_KEYS = config_loader.REQUIRED_CONFIG_KEYS


async def test_texts_validation():
    """Test texts validation with missing keys"""
    print("=" * 70)
    print("Testing TEXTS validation")
    print("=" * 70)

    # Test 1: All keys present
    print("\n✅ Test 1: All required keys present")
    valid_texts = {key: f"Test value for {key}" for key in REQUIRED_TEXT_KEYS}
    try:
        validate_texts(valid_texts)
        print("   PASSED: Validation succeeded")
    except ValueError as e:
        print(f"   FAILED: {e}")

    # Test 2: Missing one key
    print("\n❌ Test 2: Missing 'welcome_message'")
    incomplete_texts = valid_texts.copy()
    del incomplete_texts["welcome_message"]
    try:
        validate_texts(incomplete_texts)
        print("   FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   PASSED: Validation failed as expected")
        print(f"   Error message:\n{e}")

    # Test 3: Missing multiple keys
    print("\n❌ Test 3: Missing multiple keys")
    incomplete_texts = {
        "welcome_message": "test",
        "pay_button": "test"
    }
    try:
        validate_texts(incomplete_texts)
        print("   FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   PASSED: Validation failed as expected")
        print(f"   Error message:\n{e}")

    # Test 4: Empty dict
    print("\n❌ Test 4: Empty texts dict")
    try:
        validate_texts({})
        print("   FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   PASSED: Validation failed as expected")
        print(f"   Error message:\n{e}")


async def test_config_validation():
    """Test config validation with missing keys"""
    print("\n" + "=" * 70)
    print("Testing CONFIG validation")
    print("=" * 70)

    # Test 1: All keys present
    print("\n✅ Test 1: All required keys present")
    valid_config = {key: f"Test value for {key}" for key in REQUIRED_CONFIG_KEYS}
    try:
        validate_config(valid_config)
        print("   PASSED: Validation succeeded")
    except ValueError as e:
        print(f"   FAILED: {e}")

    # Test 2: Missing one key
    print("\n❌ Test 2: Missing 'TELEGRAM_GROUP_LINK'")
    incomplete_config = valid_config.copy()
    del incomplete_config["TELEGRAM_GROUP_LINK"]
    try:
        validate_config(incomplete_config)
        print("   FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   PASSED: Validation failed as expected")
        print(f"   Error message:\n{e}")

    # Test 3: Missing multiple keys
    print("\n❌ Test 3: Missing multiple keys")
    incomplete_config = {"PAYMENT_PHONE": "+7 999 123 45 67"}
    try:
        validate_config(incomplete_config)
        print("   FAILED: Should have raised ValueError")
    except ValueError as e:
        print(f"   PASSED: Validation failed as expected")
        print(f"   Error message:\n{e}")


def print_required_constants():
    """Print all required constants"""
    print("\n" + "=" * 70)
    print("REQUIRED CONSTANTS SUMMARY")
    print("=" * 70)

    print("\n📝 Required TEXT constants (lowercase, in 'action' column):")
    for i, key in enumerate(REQUIRED_TEXT_KEYS, 1):
        print(f"   {i}. {key}")

    print("\n⚙️  Required CONFIG constants (UPPERCASE, in 'action' column):")
    for i, key in enumerate(REQUIRED_CONFIG_KEYS, 1):
        print(f"   {i}. {key}")

    print("\n📋 Total: {} texts + {} config = {} constants".format(
        len(REQUIRED_TEXT_KEYS),
        len(REQUIRED_CONFIG_KEYS),
        len(REQUIRED_TEXT_KEYS) + len(REQUIRED_CONFIG_KEYS)
    ))


async def main():
    """Run all validation tests"""
    print("\n" + "🧪 " * 30)
    print("VALIDATION TEST SUITE")
    print("🧪 " * 30)

    print_required_constants()
    await test_texts_validation()
    await test_config_validation()

    print("\n" + "=" * 70)
    print("✅ All validation tests completed!")
    print("=" * 70)
    print("\n💡 TIP: Bot will now fail to start if any of these constants are missing in NocoDB")
    print("   No more silent failures with default values!\n")


if __name__ == "__main__":
    asyncio.run(main())
