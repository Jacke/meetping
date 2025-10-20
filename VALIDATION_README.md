# Configuration Validation System

## Quick Start

The bot now requires **all 8 constants** to be present in NocoDB before starting.

### Check Required Constants

```bash
python test_validation.py
```

### Required NocoDB Constants

**Texts (5)** - lowercase `action` values:
- ✅ `welcome_message`
- ✅ `pay_button`
- ✅ `payment_info`
- ✅ `success_message`
- ✅ `already_registered_message`

**Config (3)** - UPPERCASE `action` values:
- ✅ `PAYMENT_PHONE`
- ✅ `PAYMENT_AMOUNT`
- ✅ `TELEGRAM_GROUP_LINK`

### NocoDB Setup

1. Open: https://app.nocodb.com/#/wux6zxnq/pwt37o18yvtfeh6/mguawvnumqrb5k7
2. Ensure all 8 constants are present in the `action` column
3. Check values are not empty in the `text` column

### What Changed?

**Before:**
```python
# Bot would use defaults if constants were missing
TEXTS.get("welcome_message", "Default welcome...")  ❌
CONFIG.get("PAYMENT_PHONE", "+7 999 123 45 67")   ❌
```

**After:**
```python
# Bot fails to start if constants are missing
TEXTS["welcome_message"]  ✅
CONFIG["PAYMENT_PHONE"]   ✅
```

### Error Example

If constants are missing, you'll see:

```
❌ Missing required text constants in NocoDB:
   welcome_message, pay_button

Please add these text entries to NocoDB table (action column):
   Table URL: https://app.nocodb.com/#/nc/mguawvnumqrb5k7

❌ Bot cannot start without required configuration!
```

### Benefits

✅ No silent failures with default values
✅ Clear error messages showing missing constants
✅ Fail fast at startup, not during operation
✅ Production-safe configuration

## Documentation

- 📋 [REQUIRED_CONSTANTS.md](REQUIRED_CONSTANTS.md) - Full reference
- 📝 [VALIDATION_CHANGELOG.md](VALIDATION_CHANGELOG.md) - What changed
- 🧪 [test_validation.py](test_validation.py) - Test suite

## Support

If bot fails to start:
1. Check error message for missing constants
2. Verify all 8 constants exist in NocoDB
3. Ensure `.env` has correct NocoDB credentials
4. Run `python test_validation.py` to debug
