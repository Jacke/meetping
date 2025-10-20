# Required NocoDB Constants

This document lists all required text constants and configuration values that **MUST** be present in NocoDB for the payment bot to start.

The bot will **exit with an error** if any of these constants are missing.

## Overview

- **Total constants required:** 8
- **Text constants:** 5 (lowercase keys)
- **Config constants:** 3 (UPPERCASE keys)
- **NocoDB Table:** Bot Texts & Config (`mguawvnumqrb5k7`)
- **Table URL:** https://app.nocodb.com/#/wux6zxnq/pwt37o18yvtfeh6/mguawvnumqrb5k7

## Required Text Constants

All text constants use **lowercase** keys in the `action` column.

### 1. `welcome_message`
Welcome message shown to new users.

**Supports placeholders:**
- `{user.first_name}` - User's first name from Telegram

**Example:**
```
👋 Добро пожаловать, {user.first_name}!

🎉 Это бот для регистрации и оплаты билетов на наше мероприятие.

Нажмите на кнопку ниже, чтобы начать процесс оплаты.
```

### 2. `pay_button`
Text for the payment button.

**Example:**
```
💳 Оплатить билет на мероприятие
```

### 3. `payment_info`
Payment instructions shown after user clicks the payment button.

**Supports placeholders:**
- `{PAYMENT_PHONE}` - Phone number for payment (from config)
- `{PAYMENT_AMOUNT}` - Payment amount (from config)

**Example:**
```
💰 <b>Информация для оплаты:</b>

📱 Номер телефона: <code>{PAYMENT_PHONE}</code>
💵 Сумма: <b>{PAYMENT_AMOUNT}</b>

📋 <b>Инструкция:</b>
1. Переведите указанную сумму на номер телефона
2. Дождитесь подтверждения оплаты
3. После подтверждения вы получите доступ к группе мероприятия

⏳ Ожидаем подтверждения оплаты...
```

### 4. `success_message`
Message shown when payment is confirmed.

**Supports placeholders:**
- `{TELEGRAM_GROUP_LINK}` - Telegram group invitation link (from config)

**Example:**
```
✅ <b>Оплата подтверждена!</b>

🎊 Поздравляем! Ваш билет успешно оплачен.

👥 Присоединяйтесь к нашей группе:
{TELEGRAM_GROUP_LINK}

До встречи на мероприятии! 🎉
```

### 5. `already_registered_message`
Message shown to users who already registered and paid.

**Supports placeholders:**
- `{TELEGRAM_GROUP_LINK}` - Telegram group invitation link (from config)

**Example:**
```
✅ <b>Вы уже оплатили билет!</b>

👥 Ссылка на группу мероприятия:
{TELEGRAM_GROUP_LINK}

До встречи на мероприятии! 🎉
```

## Required Config Constants

All config constants use **UPPERCASE** keys in the `action` column.

### 1. `PAYMENT_PHONE`
Phone number for payment transfers.

**Format:** Any string (recommended format with country code)

**Example:**
```
+7 (999) 123-45-67
```

### 2. `PAYMENT_AMOUNT`
Ticket price. The bot extracts the numeric value from the beginning.

**Format:** `<number> <currency>`

**Example:**
```
1000 рублей
```

**Note:** The bot will extract `1000` as the price to store in the `Price` field.

### 3. `TELEGRAM_GROUP_LINK`
Telegram group invitation link for the event.

**Format:** Telegram invite link

**Example:**
```
https://t.me/+AbCdEfGhIjKlMnOp
```

## NocoDB Table Structure

The Bot Texts & Config table should have the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `action` | Text | Key name (lowercase for texts, UPPERCASE for config) |
| `text` | LongText | Value/content |

## Validation

The bot validates all required constants during startup:

1. **At bot startup**, the bot loads all texts and config from NocoDB
2. **Validation checks** that all required keys are present
3. **If any keys are missing**, the bot exits with a clear error message listing missing constants
4. **No default values** - the bot will not start with missing configuration

## Testing Validation

Run the validation test suite to verify the validation logic:

```bash
python test_validation.py
```

This will test:
- ✅ All required keys present
- ❌ Missing single key
- ❌ Missing multiple keys
- ❌ Empty configuration

## Error Messages

If constants are missing, you'll see an error like this:

```
❌ Missing required text constants in NocoDB:
   welcome_message, pay_button

Please add these text entries to NocoDB table (action column):
   Table URL: https://app.nocodb.com/#/nc/mguawvnumqrb5k7

❌ Bot cannot start without required configuration!
```

## Migration from Old System

**Before:** The bot had default values in code with `.get()`:
```python
TEXTS.get("welcome_message", "Default welcome...")  # ❌ Old way
CONFIG.get("PAYMENT_PHONE", "+7 999 123 45 67")    # ❌ Old way
```

**After:** The bot requires all values in NocoDB:
```python
TEXTS["welcome_message"]      # ✅ New way - fails if missing
CONFIG["PAYMENT_PHONE"]       # ✅ New way - fails if missing
```

## Quick Setup Checklist

- [ ] Open NocoDB table: https://app.nocodb.com/#/wux6zxnq/pwt37o18yvtfeh6/mguawvnumqrb5k7
- [ ] Add 5 text constants (lowercase `action` values)
  - [ ] `welcome_message`
  - [ ] `pay_button`
  - [ ] `payment_info`
  - [ ] `success_message`
  - [ ] `already_registered_message`
- [ ] Add 3 config constants (UPPERCASE `action` values)
  - [ ] `PAYMENT_PHONE`
  - [ ] `PAYMENT_AMOUNT`
  - [ ] `TELEGRAM_GROUP_LINK`
- [ ] Run bot to verify: `python bot_flow/flows/payment_flow.py`

## Support

If you see validation errors:
1. Check the error message for missing constants
2. Verify the `action` column values match exactly (case-sensitive)
3. Ensure NocoDB credentials are set in `.env`:
   - `NOCODB_API_TOKEN`
   - `NOCODB_TEXTS_TABLE_ID=mguawvnumqrb5k7`
   - `NOCODB_CONFIG_TABLE_ID=mguawvnumqrb5k7`
