#!/usr/bin/env python3
"""
Test script to validate payment flow without running the bot.
"""
import sys
import os

# Mock config module
class MockConfig:
    NOCODB_API_URL = "https://app.nocodb.com"
    NOCODB_API_TOKEN = "test_token"
    NOCODB_TABLE_ID = "test_table"
    NOCODB_TEXTS_TABLE_ID = "test_texts"
    NOCODB_CONFIG_TABLE_ID = "test_config"
    BOT_TOKEN = "test_bot_token"

sys.modules['config'] = type('config', (), {'config': MockConfig()})()

# Now we can import the flow builder
from bot_flow.core import FlowBuilder

# Test flow structure
def test_flow_validation():
    """Test that the flow structure is valid"""

    flow = (
        FlowBuilder("test_payment_bot")

        # State: Welcome
        .state("welcome")
            .on_command("/start")
            .on_condition(lambda ctx: ctx.get('already_registered', False), goto="route_user")
            .otherwise(goto="show_welcome")

        # State: Route User
        .state("route_user")
            .transition(
                to="already_paid",
                condition=lambda ctx: ctx.get('payment_confirmed', False)
            )
            .transition(to="payment_pending")

        # State: Show Welcome
        .state("show_welcome")
            .reply("Welcome!")
            .button("Pay", callback_data="pay", goto="ask_fullname")

        # State: Ask Fullname
        .state("ask_fullname")
            .reply("Enter your name:")
            .on_message()
            .transition(to="payment_info")

        # State: Payment Pending
        .state("payment_pending")
            .reply("Payment pending...")
            .transition(to="awaiting_payment")

        # State: Already Paid
        .state("already_paid")
            .reply("You already paid!")
            .final()

        # State: Payment Info
        .state("payment_info")
            .reply("Payment info...")
            .transition(to="awaiting_payment")

        # State: Awaiting Payment
        .state("awaiting_payment")
            .poll(lambda ctx: False, interval=60)
            .on_condition(lambda ctx: ctx.poll_result, goto="success")

        # State: Success
        .state("success")
            .reply("Success!")
            .final()

        # State: Stats
        .state("stats")
            .on_command("/stats")
            .final()

        .build()
    )

    print("✅ Flow validation passed!")
    print(f"   States: {len(flow.states)}")
    print(f"   Start state: {flow.start_state}")

    # Print state list
    print("\n📋 States:")
    for state_name in flow.states.keys():
        print(f"   - {state_name}")

    return flow

if __name__ == "__main__":
    try:
        flow = test_flow_validation()
        print("\n🎉 All validation checks passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
