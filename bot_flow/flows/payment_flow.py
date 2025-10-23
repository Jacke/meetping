"""
Declarative payment bot flow definition.

This is the payment_bot.py reimplemented using the declarative FlowBuilder API.
"""
import httpx
from config import config
from bot_flow.core import FlowBuilder, FlowContext
from bot_flow.flows.texts_loader import load_texts_from_nocodb
from bot_flow.flows.config_loader import load_config_from_nocodb

# NocoDB configuration from centralized config
NOCODB_API_URL = config.NOCODB_API_URL
NOCODB_API_TOKEN = config.NOCODB_API_TOKEN
NOCODB_TABLE_ID = config.NOCODB_TABLE_ID

# Global storage (loaded from NocoDB at startup)
TEXTS = {}
CONFIG = {}


# ============================================================================
# Actions - Business logic functions
# ============================================================================

async def save_fullname_from_message(ctx: FlowContext) -> None:
    """Save user's full name from message text to context"""
    message_text = ctx.get('message_text', '').strip()
    if message_text:
        ctx.set('fullname', message_text)
        print(f"✅ Saved fullname for user {ctx.user.id}: {message_text}")
    else:
        # If no text provided, use Telegram first name as fallback
        ctx.set('fullname', ctx.user.first_name or "Unknown")
        print(f"⚠️ No fullname provided, using fallback: {ctx.user.first_name}")


async def create_payment_record(ctx: FlowContext) -> None:
    """Create payment record in NocoDB and store record_id in context"""
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB not configured, local mode")
        ctx.set('record_id', None)
        return

    headers = {
        "xc-token": NOCODB_API_TOKEN,
        "Content-Type": "application/json"
    }

    # Get payment amount from config (validated at startup, no default needed)
    payment_amount = CONFIG["PAYMENT_AMOUNT"]
    # Extract numeric value from string like "1000 рублей"
    price = int(payment_amount.split()[0])

    # Get fullname from context (saved from message)
    fullname = ctx.get('fullname', ctx.user.first_name or "Unknown")

    data = {
        "TG": ctx.user.username or "",
        "TG ID": ctx.user.id,
        "FullName": fullname,
        "Price": price,
        "Paid": False
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                json=data,
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            record_id = str(result.get("Id") or result.get("id"))
            ctx.set('record_id', record_id)
            print(f"✅ Created NocoDB record: {record_id} for user {ctx.user.id} ({fullname})")
    except Exception as e:
        print(f"❌ Error creating NocoDB record: {e}")
        ctx.set('record_id', None)


async def reload_texts_and_config(ctx: FlowContext) -> None:
    """Reload texts and config from NocoDB on each /start"""
    global TEXTS, CONFIG
    TEXTS = await load_texts_from_nocodb()
    CONFIG = await load_config_from_nocodb()

    # Store in context for dynamic usage
    ctx.set('texts', TEXTS)
    ctx.set('config', CONFIG)

    print(f"🔄 Reloaded texts and config from NocoDB for user {ctx.user.id}")


async def check_if_payment_confirmed(ctx: FlowContext) -> bool:
    """
    Check if user's payment is confirmed (from context).
    This is a simple check of the payment_confirmed flag set during registration check.

    Returns True if payment is confirmed, False otherwise.
    """
    return ctx.get('payment_confirmed', False)


async def load_awaiting_payment_users() -> list:
    """
    Load all users from NocoDB who are awaiting payment (Paid = false).
    Returns list of dicts with user data: [{tg_id, record_id, username, first_name}, ...]
    """
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB not configured, skipping user state restoration")
        return []

    headers = {"xc-token": NOCODB_API_TOKEN}

    try:
        async with httpx.AsyncClient() as client:
            # Get all records with Paid = false
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                params={
                    "where": "(Paid,eq,false)",  # Filter: Paid = false
                    "limit": 1000
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            records = data.get("list", [])

            users = []
            for record in records:
                tg_id = record.get("TG ID")
                if tg_id:
                    users.append({
                        'tg_id': int(tg_id),
                        'record_id': str(record.get("Id") or record.get("id")),
                        'username': record.get("TG", ""),
                        'first_name': record.get("First Name", "Unknown")
                    })

            return users

    except Exception as e:
        print(f"❌ Error loading awaiting payment users: {e}")
        return []


async def get_statistics(ctx: FlowContext) -> None:
    """
    Get statistics from NocoDB and send to user.
    This command is only available to admins.
    """
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        await ctx.update.message.reply_text(
            "⚠️ NocoDB не настроен",
            parse_mode="HTML"
        )
        return

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            # Get all records
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                params={"limit": 1000},  # Get up to 1000 records
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            records = data.get("list", [])

            # Calculate statistics
            total = len(records)
            paid = sum(1 for r in records if r.get("Paid") is True)
            unpaid = total - paid

            # Format message
            message = f"""
📊 <b>Статистика регистраций</b>

📝 Всего заявок: <b>{total}</b>
✅ Оплачено: <b>{paid}</b>
⏳ Ожидают оплаты: <b>{unpaid}</b>

🔗 <a href="{NOCODB_API_URL}/#/nc/{NOCODB_TABLE_ID}">Открыть NocoDB</a>
"""

            await ctx.update.message.reply_text(
                message,
                parse_mode="HTML",
                disable_web_page_preview=True
            )

    except Exception as e:
        await ctx.update.message.reply_text(
            f"❌ Ошибка получения статистики: {e}",
            parse_mode="HTML"
        )


async def check_user_registration(ctx: FlowContext) -> bool:
    """
    Check if user is already registered (has a record in NocoDB).

    Sets context variables:
    - 'already_registered': True if user has a record
    - 'payment_confirmed': True if user has paid
    - 'record_id': NocoDB record ID if found

    Returns True if user is registered (paid or unpaid), False otherwise.
    This is used as a polling check function that runs immediately.
    """
    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB not configured, skipping registration check")
        return False

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            # Search for records with this user's Telegram ID
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records",
                headers=headers,
                params={
                    "where": f"(TG ID,eq,{ctx.user.id})",
                    "limit": 1
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # Check if any records found
            records = data.get("list", [])
            if records:
                record = records[0]
                record_id = str(record.get("Id") or record.get("id"))
                is_paid = record.get("Paid", False) is True

                # Store record info in context
                ctx.set('record_id', record_id)
                ctx.set('already_registered', True)
                ctx.set('payment_confirmed', is_paid)

                print(f"✅ Found existing registration for user {ctx.user.id}, record: {record_id}, paid: {is_paid}")
                return True  # User is registered (paid or unpaid)

            print(f"ℹ️ No existing registration for user {ctx.user.id}")
            ctx.set('already_registered', False)
            ctx.set('payment_confirmed', False)
            return False  # User is not registered

    except Exception as e:
        print(f"❌ Error checking user registration: {e}")
        ctx.set('already_registered', False)
        ctx.set('payment_confirmed', False)
        return False  # On error, treat as not registered


async def check_payment_status(ctx: FlowContext) -> bool:
    """
    Check if payment is confirmed in NocoDB.
    Returns True if paid, False otherwise.
    """
    record_id = ctx.get('record_id')

    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID or not record_id:
        return False

    headers = {
        "xc-token": NOCODB_API_TOKEN
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOCODB_API_URL}/api/v2/tables/{NOCODB_TABLE_ID}/records/{record_id}",
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            is_paid = data.get("Paid", False) is True

            if is_paid:
                print(f"✅ Payment confirmed for user {ctx.user.id}")

            return is_paid
    except Exception as e:
        print(f"❌ Error checking payment status: {e}")
        return False


# ============================================================================
# Flow Definition
# ============================================================================

async def build_payment_flow() -> 'Flow':
    """
    Build the payment bot flow declaratively.

    Flow structure:
        welcome
          ├─> already_paid (if user registered AND paid)
          ├─> payment_pending -> awaiting_payment (if user registered BUT NOT paid)
          └─> show_welcome -> ask_fullname -> collect_fullname -> payment_info -> awaiting_payment -> success (if new user)

    States:
    - welcome: Check registration status
    - show_welcome: New user welcome with payment button
    - ask_fullname: Ask user for their full name (Фамилия и Имя)
    - collect_fullname: Collect full name from message text
    - payment_pending: User started payment but hasn't completed (shows payment instructions)
    - already_paid: User already completed payment
    - payment_info: Create payment record and show payment instructions
    - awaiting_payment: Polling for payment confirmation
    - success: Payment confirmed

    Raises:
        ValueError: If required texts or config are missing in NocoDB
    """
    # Load texts and config from NocoDB (will raise ValueError if validation fails)
    global TEXTS, CONFIG
    print("\n📥 Loading texts and config from NocoDB...")
    TEXTS = await load_texts_from_nocodb()
    CONFIG = await load_config_from_nocodb()
    print("✅ Texts and config validated successfully\n")

    # Format payment_info with actual values from config (no defaults)
    payment_info_text = TEXTS["payment_info"].format(
        PAYMENT_PHONE=CONFIG["PAYMENT_PHONE"],
        PAYMENT_AMOUNT=CONFIG["PAYMENT_AMOUNT"]
    )

    # Format success message with group link from config (no defaults)
    success_text = TEXTS["success_message"].format(
        TELEGRAM_GROUP_LINK=CONFIG["TELEGRAM_GROUP_LINK"]
    )

    flow = (
        FlowBuilder("payment_bot")

        # ====================================================================
        # State: Welcome (checks registration with immediate poll)
        # ====================================================================
        .state("welcome")
            .on_command("/start")
            .action(reload_texts_and_config)
            .poll(check_user_registration, interval=1)  # Check with minimal interval
            .on_condition(lambda ctx: ctx.poll_result, goto="route_user")
            .otherwise(goto="show_welcome")

        # ====================================================================
        # State: Route User (decides where to send based on payment status)
        # ====================================================================
        .state("route_user")
            .poll(check_if_payment_confirmed, interval=1)
            .on_condition(lambda ctx: ctx.poll_result, goto="already_paid")
            .otherwise(goto="payment_pending")

        # ====================================================================
        # State: Show Welcome (for new users)
        # ====================================================================
        .state("show_welcome")
            .reply(TEXTS["welcome_message"])
            .button(
                TEXTS["pay_button"],
                callback_data="pay_ticket",
                goto="ask_fullname"
            )

        # ====================================================================
        # State: Ask Full Name (collect user's full name)
        # ====================================================================
        .state("ask_fullname")
            .on_callback("pay_ticket")
            .reply("📝 Пожалуйста, напишите ваши Фамилию и Имя:")
            .transition(to="collect_fullname")

        # ====================================================================
        # State: Collect Full Name (receives message with full name)
        # ====================================================================
        .state("collect_fullname")
            .on_message()
            .action(save_fullname_from_message)
            .transition(to="payment_info")

        # ====================================================================
        # State: Payment Pending (user registered but not paid)
        # Shows same payment instructions as payment_info
        # ====================================================================
        .state("payment_pending")
            .reply(payment_info_text, parse_mode="HTML")
            .transition(to="awaiting_payment")

        # ====================================================================
        # State: Already Paid
        # ====================================================================
        .state("already_paid")
            .reply(
                TEXTS["already_registered_message"].format(
                    TELEGRAM_GROUP_LINK=CONFIG["TELEGRAM_GROUP_LINK"]
                ),
                parse_mode="HTML"
            )
            .final()

        # ====================================================================
        # State: Payment Info
        # ====================================================================
        .state("payment_info")
            .action(create_payment_record)
            .reply(payment_info_text, parse_mode="HTML")
            .transition(to="awaiting_payment")

        # ====================================================================
        # State: Awaiting Payment (with polling)
        # ====================================================================
        .state("awaiting_payment")
            .poll(check_payment_status, interval=10)
            .on_condition(lambda ctx: ctx.poll_result, goto="success")

        # ====================================================================
        # State: Success
        # ====================================================================
        .state("success")
            .reply(success_text, parse_mode="HTML")
            .final()

        # ====================================================================
        # State: Stats (Admin only)
        # ====================================================================
        .state("stats")
            .on_command("/stats")
            .action(get_statistics)
            .final()

        .build()
    )

    return flow


# ============================================================================
# Main - Run bot or export visualization
# ============================================================================

def main():
    """Main entry point"""
    import sys
    import asyncio

    # Check if we should just visualize
    if len(sys.argv) > 1 and sys.argv[1] == "visualize":
        async def visualize_flow():
            from bot_flow.core import visualize
            try:
                flow = await build_payment_flow()
                visualizer = visualize(flow)

                # Export all formats
                visualizer.export_mermaid("docs/payment_flow.md")
                visualizer.export_graphviz("docs/payment_flow.dot")
                visualizer.export_ascii("docs/payment_flow.txt")

                print("\n📊 Visualization exported!")
                print("   - docs/payment_flow.md (Mermaid)")
                print("   - docs/payment_flow.dot (GraphViz)")
                print("   - docs/payment_flow.txt (ASCII)")
            except ValueError as e:
                print(f"\n{e}")
                sys.exit(1)

        asyncio.run(visualize_flow())
        return

    # Run the bot
    from bot_flow.core import FlowExecutor

    BOT_TOKEN = config.BOT_TOKEN
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
        sys.exit(1)

    # Build flow (loads texts from NocoDB with validation) - run in asyncio
    try:
        flow = asyncio.run(build_payment_flow())
    except ValueError as e:
        print(f"\n{e}")
        print("\n❌ Bot cannot start without required configuration!")
        sys.exit(1)

    # Load users awaiting payment from NocoDB
    print("\n📥 Loading users in awaiting_payment state from NocoDB...")
    awaiting_users = asyncio.run(load_awaiting_payment_users())
    if awaiting_users:
        print(f"📊 Found {len(awaiting_users)} users awaiting payment:")
        for user in awaiting_users:
            print(f"   • User {user['tg_id']} (@{user['username'] or user['first_name']}) - record {user['record_id']}")
    else:
        print("✓ No users awaiting payment")

    # Admin Chat IDs for notifications
    # To get your Chat ID:
    # 1. Send /start to @userinfobot in Telegram
    # 2. Copy your ID from the response
    # 3. Replace the placeholders below with your actual Chat IDs
    admin_chat_ids = [
        53170594,  # @stansob - Replace with actual Chat ID
        1774280912,  # @Haleecolemax2 - Replace with actual Chat ID
    ]

    # Create executor
    executor = FlowExecutor(
        flow,
        BOT_TOKEN,
        admin_chat_ids=admin_chat_ids,
        nocodb_url=NOCODB_API_URL,
        nocodb_table_id=NOCODB_TABLE_ID
    )

    # Restore user states and start polling (must be done in async context)
    # This will be called in post_init hook
    executor._awaiting_users = awaiting_users

    # Run executor (this creates its own event loop)
    executor.run()


if __name__ == "__main__":
    main()
