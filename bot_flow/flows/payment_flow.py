"""
Declarative payment bot flow definition.

This is the payment_bot.py reimplemented using the declarative FlowBuilder API.
"""
import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

from bot_flow.core import FlowBuilder, FlowContext

# Load environment
env_file_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_file_path)

# Configuration
NOCODB_API_URL = os.getenv("NOCODB_API_URL", "https://app.nocodb.com")
NOCODB_API_TOKEN = os.getenv("NOCODB_API_TOKEN")
NOCODB_TABLE_ID = os.getenv("NOCODB_TABLE_ID")
PAYMENT_PHONE = os.getenv("PAYMENT_PHONE", "+7 (999) 123-45-67")
PAYMENT_AMOUNT = os.getenv("PAYMENT_AMOUNT", "1000 рублей")
TELEGRAM_GROUP_LINK = os.getenv("TELEGRAM_GROUP_LINK", "https://t.me/your_group_link")


# ============================================================================
# Actions - Business logic functions
# ============================================================================

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

    data = {
        "TG": ctx.user.username or "",
        "TG ID": ctx.user.id,
        "Price": int(PAYMENT_AMOUNT.split()[0]) if PAYMENT_AMOUNT else 1000,
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
            print(f"✅ Created NocoDB record: {record_id} for user {ctx.user.id}")
    except Exception as e:
        print(f"❌ Error creating NocoDB record: {e}")
        ctx.set('record_id', None)


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

def build_payment_flow() -> 'Flow':
    """
    Build the payment bot flow declaratively.

    Flow structure:
        welcome -> payment_info -> awaiting_payment -> success
    """
    flow = (
        FlowBuilder("payment_bot")

        # ====================================================================
        # State: Welcome
        # ====================================================================
        .state("welcome")
            .on_command("/start")
            .reply(
                "👋 Добро пожаловать, {user.first_name}!\n\n"
                "🎉 Это бот для регистрации и оплаты билетов на наше мероприятие.\n\n"
                "Нажмите на кнопку ниже, чтобы начать процесс оплаты."
            )
            .button("💳 Оплатить билет на мероприятие", callback_data="pay_ticket", goto="payment_info")

        # ====================================================================
        # State: Payment Info
        # ====================================================================
        .state("payment_info")
            .on_callback("pay_ticket")
            .action(create_payment_record)
            .reply(
                "💰 <b>Информация для оплаты:</b>\n\n"
                f"📱 Номер телефона: <code>{PAYMENT_PHONE}</code>\n"
                f"💵 Сумма: <b>{PAYMENT_AMOUNT}</b>\n\n"
                "📋 <b>Инструкция:</b>\n"
                "1. Переведите указанную сумму на номер телефона\n"
                "2. Дождитесь подтверждения оплаты\n"
                "3. После подтверждения вы получите доступ к группе мероприятия\n\n"
                "⏳ Ожидаем подтверждения оплаты...",
                parse_mode="HTML"
            )
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
            .reply(
                "✅ <b>Оплата подтверждена!</b>\n\n"
                "🎊 Поздравляем! Ваш билет успешно оплачен.\n\n"
                "👥 Присоединяйтесь к нашей группе:\n"
                f"{TELEGRAM_GROUP_LINK}\n\n"
                "До встречи на мероприятии! 🎉",
                parse_mode="HTML"
            )
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

    # Check if we should just visualize
    if len(sys.argv) > 1 and sys.argv[1] == "visualize":
        from bot_flow.core import visualize

        flow = build_payment_flow()
        visualizer = visualize(flow)

        # Export all formats
        visualizer.export_mermaid("docs/payment_flow.md")
        visualizer.export_graphviz("docs/payment_flow.dot")
        visualizer.export_ascii("docs/payment_flow.txt")

        print("\n📊 Visualization exported!")
        print("   - docs/payment_flow.md (Mermaid)")
        print("   - docs/payment_flow.dot (GraphViz)")
        print("   - docs/payment_flow.txt (ASCII)")
        return

    # Run the bot
    from bot_flow.core import FlowExecutor

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
        return

    if not NOCODB_API_TOKEN or not NOCODB_TABLE_ID:
        print("⚠️ NocoDB not configured. Working in local mode.")
        print("   Add NOCODB_API_TOKEN and NOCODB_TABLE_ID to .env for full functionality")

    # Build flow
    flow = build_payment_flow()

    # Create and run executor
    executor = FlowExecutor(flow, BOT_TOKEN)
    executor.run()


if __name__ == "__main__":
    main()
