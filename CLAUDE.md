# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MeetPing-Pay** is a Python-based payment processing bot system for event tickets. The repository contains:
- Python Telegram payment bot implementation
- MCP testing utilities

## Environment Configuration

All environment variables are centralized in `config.py` module. Variables are loaded from `.env` file at project root.

### Required Variables
- `BOT_TOKEN` - Telegram bot authentication token

### Optional Variables
- `LOG_FILE` - Path to log file (default: logs/bot.log)
- `OPENAI_API_KEY` - OpenAI API key for agent functionality
- `ENV` - Environment mode (default: dev)
- `DATABASE_URL` - Database connection string

### NocoDB Configuration
- `NOCODB_API_URL` - NocoDB API endpoint (default: https://app.nocodb.com)
- `NOCODB_API_TOKEN` - NocoDB authentication token
- `NOCODB_TABLE_ID` - Table ID for payment records (mfaob33z2nnrxve)

### NocoDB Tables
- **Payment Records** (`mfaob33z2nnrxve`) - Stores payment records with user data
  - `TG ID` - Telegram user ID (used for checking existing registrations)
  - `TG` - Telegram username
  - `Price` - Ticket price
  - `Paid` - Payment status (boolean/toggle)
- **Bot Texts & Config** (`mguawvnumqrb5k7`) - Stores all bot messages and configuration (action -> text)
  - **Text Messages** (lowercase action) - ⚠️ REQUIRED:
    - `welcome_message` - Welcome message with {user.first_name} placeholder
    - `pay_button` - Payment button text
    - `payment_info` - Payment instructions with {PAYMENT_PHONE} and {PAYMENT_AMOUNT} placeholders
    - `success_message` - Success message with {TELEGRAM_GROUP_LINK} placeholder
    - `already_registered_message` - Message for users who already registered
  - **Configuration** (uppercase action) - ⚠️ REQUIRED:
    - `PAYMENT_PHONE` - Phone number for payment transfers
    - `PAYMENT_AMOUNT` - Ticket price
    - `TELEGRAM_GROUP_LINK` - Event group invitation link

⚠️ **IMPORTANT:** All 8 constants above are REQUIRED. Bot will not start if any are missing.
See [REQUIRED_CONSTANTS.md](REQUIRED_CONSTANTS.md) for detailed documentation.

### Configuration Module
All bots import configuration from centralized `config.py`:
```python
from config import config

BOT_TOKEN = config.BOT_TOKEN
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
```

## Current Architecture

### Python Bots

**bot_flow/flows/payment_flow.py** - Main payment processing bot (declarative flow version):
- `/start` - Welcome message with payment button (visible in Telegram command menu)
- `/stats` - Admin-only command for viewing registration statistics
- Checks if user is already registered (prevents duplicate registrations)
- Creates payment record in NocoDB with user data
- Polls NocoDB every 10 seconds to check payment status
- **State restoration:** Automatically restores polling for all users in `awaiting_payment` state on bot restart
- Automatic payment confirmation when toggle is switched in NocoDB
- **Startup validation:** Validates all required texts and config from NocoDB at startup
- All texts and config loaded dynamically from NocoDB (no default values)
- Built with declarative FlowBuilder API (~40 lines vs 232 lines imperative)
- Supports graceful shutdown with Ctrl+C
- **Admin notifications:** Sends state change notifications with NocoDB link to admins

**agent.py** - Homework guardrail agent example using Anthropic Agents SDK
**mcp-test.py** - LangChain + OpenAI integration

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Graceful Shutdown

All bots support graceful shutdown on `SIGINT` (Ctrl+C) and `SIGTERM` signals:

**Features:**
- Handles `SIGINT` (Ctrl+C) and `SIGTERM` signals
- Cancels all active polling/background tasks
- Waits for tasks to complete cleanup
- Properly stops and shuts down Telegram application
- Clean exit without errors

**Implementation:**

- [bot_flow/core/executor.py](bot_flow/core/executor.py) - Cancels all polling tasks in flow executor
- [bot_flow/flows/payment_flow.py](bot_flow/flows/payment_flow.py) - Payment check tasks stop gracefully

**Testing:**

```bash
python test_graceful_shutdown.py  # Test graceful shutdown demo
# Press Ctrl+C to see graceful shutdown in action
```

## Running Bots

### Main Entry Point

All bots can be run through the unified `main.py` entry point:

```bash
# Run payment bot (default)
python main.py
python main.py payment

# Run homework agent
python main.py agent

# Run MCP test agent
python main.py mcp-test

# Generate flow visualization
python main.py visualize

# Check configuration status
python main.py status

# Show help
python main.py help
```

### Direct Execution

Individual bots can still be run directly:

```bash
python bot_flow/flows/payment_flow.py   # Payment bot (declarative flow)
python agent.py                         # Agent example
python mcp-test.py                      # MCP test
```

## Payment Bot Flow

### Flow Logic

```
/start
  ├─> Already Paid (if user registered AND paid)
  │   └─> Show group link, END
  │
  ├─> Payment Pending (if user registered BUT NOT paid)
  │   └─> "Waiting for confirmation" → Poll status → Success
  │
  └─> New User (not registered)
      └─> Welcome → Click "Pay" → Payment Info → Poll status → Success
```

### Detailed Steps

1. **User sends `/start`** → Bot checks if user is already registered in NocoDB
2. **If registered AND paid** → Show "already paid" message with group link (END)
3. **If registered BUT NOT paid** → Show "payment pending" message → Continue polling
4. **If new user** → Show welcome message with "Оплатить билет" button
5. User clicks button → Bot creates record in NocoDB with user_id, username, first_name
6. Payment info displayed (phone, amount) with instructions
7. Background task polls NocoDB every 10 seconds checking the "Paid" toggle field
8. Admin switches toggle to true in NocoDB
9. Bot detects payment confirmation and sends success message with Telegram group link

**NocoDB Admin Panel:** <https://app.nocodb.com/#/wux6zxnq/pwt37o18yvtfeh6/mfaob33z2nnrxve>

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

## Bot Flow Framework (NEW)

**bot_flow/** - Declarative framework for building Telegram bots with automatic flow visualization

### Overview

The `bot_flow` framework provides a Graph Builder API for creating Telegram bots declaratively:
- **Fluent API** - Build bot flows with chainable methods
- **Auto visualization** - Generate Mermaid/GraphViz diagrams from code
- **Polling support** - Built-in polling for async checks (payments, timers)
- **Validation** - Flow validation at build time, not runtime
- **Type hints** - Full IDE support with autocomplete

### Structure

```
bot_flow/
├── core/
│   ├── state.py          # StateNode, Flow, PollingConfig
│   ├── builder.py        # FlowBuilder, StateBuilder (Fluent API)
│   ├── executor.py       # FlowExecutor (runs flow with python-telegram-bot)
│   └── visualizer.py     # FlowVisualizer (Mermaid/GraphViz export)
├── flows/
│   └── payment_flow.py   # Declarative payment_bot implementation
├── examples/
│   └── demo.py           # 5 example bots (welcome, survey, menu, timer, age_gate)
└── README.md             # Full API documentation
```

### Quick Example

```python
from bot_flow.core import FlowBuilder, FlowExecutor

flow = (
    FlowBuilder("my_bot")
    .state("start")
        .on_command("/start")
        .reply("Hello!")
        .button("Next", goto="next")
    .state("next")
        .reply("Done!")
        .final()
    .build()
)

# Visualize
flow.visualize().export_mermaid("flow.md")

# Run
FlowExecutor(flow, bot_token).run()
```

### Usage

```bash
# Visualize payment_bot flow
python3 visualize_payment_flow.py
# Generates: docs/payment_flow.md, docs/payment_flow.dot, docs/payment_flow.txt

# Run example bots
python3 bot_flow/examples/demo.py visualize  # Generate all examples
python3 bot_flow/examples/demo.py run menu   # Run menu bot

# Run declarative payment bot
python3 bot_flow/flows/payment_flow.py       # Normal mode
python3 bot_flow/flows/payment_flow.py visualize  # Generate diagrams
```

### Documentation

- **API Reference**: [bot_flow/README.md](bot_flow/README.md)
- **Full Guide**: [docs/FLOW_BUILDER_GUIDE.md](docs/FLOW_BUILDER_GUIDE.md)
- **Approaches Comparison**: [docs/DECLARATIVE_BOT_APPROACHES.md](docs/DECLARATIVE_BOT_APPROACHES.md)
- **Payment Flow Diagram**: [docs/payment_flow.md](docs/payment_flow.md)

### Key Features

1. **Declarative Flow Definition**
   - Define bot flow as a graph of states
   - ~40 lines vs 232 lines of imperative code

2. **Automatic Visualization**
   - Generate Mermaid state diagrams
   - Export GraphViz DOT files
   - ASCII diagrams for terminal

3. **Polling Support**
   - Built-in polling for async operations
   - Example: Check payment status every 10 seconds
   - Conditional transitions based on poll results

4. **Context Management**
   - FlowContext object for storing user data
   - Access to user info, environment vars
   - Template variables in messages: `{user.first_name}`

5. **Flow Validation**
   - Validates state transitions at build time
   - Checks for unreachable states
   - Ensures all transitions point to valid states

### Comparison: Imperative vs Declarative

**payment_bot.py** (Imperative - 232 lines):
- Logic scattered across functions
- Hard to visualize flow
- No automatic diagram generation

**bot_flow/flows/payment_flow.py** (Declarative - ~40 lines):
- Entire flow visible at once
- Auto-generates flow diagrams
- Easy to test and maintain

See [docs/DECLARATIVE_BOT_APPROACHES.md](docs/DECLARATIVE_BOT_APPROACHES.md) for detailed comparison.
