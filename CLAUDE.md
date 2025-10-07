# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MeetPing-Pay** is a Python-based payment processing bot system for event tickets. The repository contains:
- Python Telegram payment bot implementation
- MCP testing utilities

## Environment Configuration

All bots load environment variables from `.env` file located at project root:
- `BOT_TOKEN` / `TELEGRAM_TOKEN` - Telegram bot authentication token
- `LOG_FILE` - Path to log file
- `OPENAI_API_KEY` - OpenAI API key for agent functionality

### NocoDB Configuration (payment_bot.py)
- `NOCODB_API_URL` - NocoDB API endpoint (default: https://app.nocodb.com)
- `NOCODB_API_TOKEN` - NocoDB authentication token
- `NOCODB_TABLE_ID` - Table ID for payment records

### Payment Settings (payment_bot.py)
- `PAYMENT_PHONE` - Phone number for payment transfers
- `PAYMENT_AMOUNT` - Ticket price
- `TELEGRAM_GROUP_LINK` - Event group invitation link

Environment file pattern: `Path(__file__).resolve().parent.parent / ".env"` for payment_bot.py

## Current Architecture

### Python Bots

**payment_bot.py** - Main payment processing bot with NocoDB integration:
- `/start` - Welcome message with payment button
- Callback handler for payment initiation
- Creates payment record in NocoDB with user data
- Polls NocoDB every 10 seconds to check payment status
- Admin commands: `/confirm <user_id>`, `/pending`
- Automatic payment confirmation when toggle is switched in NocoDB

**agent.py** - Homework guardrail agent example using Anthropic Agents SDK
**mcp-test.py** - LangChain + OpenAI integration

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running Bots

```bash
# Payment bot
python payment_bot.py

# MCP test agent
python mcp-test.py

# Agent example
python agent.py
```

## Payment Bot Flow

1. User sends `/start` → Welcome message with "Оплатить билет" button
2. User clicks button → Bot creates record in NocoDB with user_id, username, first_name
3. Payment info displayed (phone, amount), user added to `pending_payments`
4. Background task polls NocoDB every 10 seconds checking the "paid" toggle field
5. Admin switches toggle to true in NocoDB (https://app.nocodb.com/#/wux6zxnq/pwt37o18yvtfeh6/mfaob33z2nnrxve)
6. Bot detects payment confirmation and sends success message with Telegram group link

## NocoDB Integration

The bot integrates with NocoDB to track payment status:

### API Endpoints Used (v2 API)
- `POST /api/v2/tables/{table_id}/records` - Create payment record
- `GET /api/v2/tables/{table_id}/records/{record_id}` - Check payment status
- `PATCH /api/v2/tables/{table_id}/records/{record_id}` - Update payment status

### Required NocoDB Table Fields
- `TG` (Text) - Telegram username
- `TG ID` (Number) - Telegram user ID
- `Price` (Number) - Ticket price
- `Paid` (Checkbox/Boolean) - Payment status toggle
- `CreatedAt` (DateTime) - Auto-generated creation timestamp
- `UpdatedAt` (DateTime) - Auto-generated update timestamp

### Setup Steps
1. Create NocoDB table with required fields
2. Get API token from NocoDB settings
3. Get table ID from URL or API
4. Update `.env` with `NOCODB_API_TOKEN` and `NOCODB_TABLE_ID`

## Local Development

Bot works in local mode without NocoDB configuration. To enable full functionality, configure NocoDB variables in `.env`.

## Testing

### Unit Tests (Mocked)
Tests with mocked dependencies, fast execution:

```bash
# Run all unit tests
pytest test_payment_bot.py -v

# Run specific test
pytest test_payment_bot.py::TestPaymentBot::test_start_command -v

# Run with coverage
pytest test_payment_bot.py --cov=payment_bot --cov-report=html
```

### Integration Tests (Real NocoDB API)
Tests with real NocoDB API, requires configuration in `.env.test`:

```bash
# Configure .env.test first
# NOCODB_API_TOKEN=your_token
# NOCODB_TABLE_ID=your_table_id

# Run integration tests
pytest test_integration_nocodb.py -v -s

# Run specific integration test
pytest test_integration_nocodb.py::TestNocoDBIntegration::test_payment_workflow -v -s
```

**What integration tests cover:**
- ✅ Create payment record in real NocoDB
- ✅ Read payment record from NocoDB
- ✅ Update payment status (toggle paid field)
- ✅ List all payment records
- ✅ Full payment workflow simulation
- ✅ API error handling
- ✅ Connection validation

**Note:** Integration tests automatically clean up created test records after execution.
