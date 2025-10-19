#!/usr/bin/env python3
"""Test payment flow building"""
import asyncio
import sys


async def main():
    print("🧪 Testing payment flow build...")

    # Import flow building function
    from bot_flow.flows.payment_flow import build_payment_flow

    try:
        # Build flow
        flow = await build_payment_flow()

        print(f"✅ Flow built successfully!")
        print(f"   Name: {flow.name}")
        print(f"   States: {len(flow.states)}")
        print(f"   Initial state: {flow.initial_state}")

        # List all states
        print(f"\n📊 States:")
        for state_name, state in flow.states.items():
            triggers = []
            if state.trigger_type:
                triggers.append(f"{state.trigger_type.value}: {state.trigger_value}")
            if state.polling:
                triggers.append("polling")

            trigger_info = f" ({', '.join(triggers)})" if triggers else ""
            print(f"   - {state_name}{trigger_info}")

            # Check if welcome state has correct polling config
            if state_name == "welcome" and state.polling:
                print(f"     Polling interval: {state.polling.interval}s")
                print(f"     on_true_goto: {state.polling.on_true_goto}")
                print(f"     on_false_goto: {state.polling.on_false_goto}")

        return 0

    except Exception as e:
        print(f"❌ Error building flow: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
