"""
Demo: Simple bot examples using FlowBuilder API

This file demonstrates various bot patterns using declarative flows.
"""
import os
from dotenv import load_dotenv
from bot_flow.core import FlowBuilder, FlowContext, FlowExecutor, visualize

load_dotenv()


# ============================================================================
# Example 1: Simple Welcome Bot
# ============================================================================

def example_welcome_bot():
    """Minimal bot with welcome message and button"""
    flow = (
        FlowBuilder("welcome_bot")

        .state("start")
            .on_command("/start")
            .reply("👋 Hello! I'm a simple bot.")
            .button("Say Hi", goto="greet")

        .state("greet")
            .reply("Hi there! Nice to meet you! 😊")
            .final()

        .build()
    )

    return flow


# ============================================================================
# Example 2: Survey Bot with Multiple Steps
# ============================================================================

async def save_name(ctx: FlowContext):
    """Save user's name from message text"""
    # In real implementation, you'd extract text from update
    ctx.set('name', 'User')  # Placeholder


async def save_age(ctx: FlowContext):
    """Save user's age"""
    ctx.set('age', '25')  # Placeholder


def example_survey_bot():
    """Multi-step survey bot"""
    flow = (
        FlowBuilder("survey_bot")

        .state("start")
            .on_command("/start")
            .reply("📝 Let's start a quick survey!\n\nWhat's your name?")
            .button("Skip", goto="ask_age")

        .state("ask_age")
            .action(save_name)
            .reply("How old are you?")
            .button("Skip", goto="summary")

        .state("summary")
            .action(save_age)
            .reply(
                "✅ Thanks for completing the survey!\n\n"
                "Name: {ctx.name}\n"
                "Age: {ctx.age}"
            )
            .final()

        .build()
    )

    return flow


# ============================================================================
# Example 3: Menu Bot with Multiple Paths
# ============================================================================

def example_menu_bot():
    """Bot with menu and multiple navigation paths"""
    flow = (
        FlowBuilder("menu_bot")

        .state("main_menu")
            .on_command("/start")
            .reply("🏠 Main Menu\n\nChoose an option:")
            .button("📖 About", callback_data="about", goto="about")
            .button("⚙️ Settings", callback_data="settings", goto="settings")
            .button("❓ Help", callback_data="help", goto="help")

        .state("about")
            .reply("ℹ️ This is a demo menu bot.\n\nVersion 1.0")
            .button("🔙 Back to Menu", callback_data="back", goto="main_menu")

        .state("settings")
            .reply("⚙️ Settings\n\n(Settings options would go here)")
            .button("🔙 Back to Menu", callback_data="back", goto="main_menu")

        .state("help")
            .reply(
                "❓ Help\n\n"
                "Available commands:\n"
                "/start - Show main menu\n"
                "/help - Show this help"
            )
            .button("🔙 Back to Menu", callback_data="back", goto="main_menu")

        .build()
    )

    return flow


# ============================================================================
# Example 4: Timer Bot with Polling
# ============================================================================

import asyncio
import time

async def start_timer(ctx: FlowContext):
    """Start a timer"""
    ctx.set('start_time', time.time())
    ctx.set('duration', 5)  # 5 seconds


async def check_timer_done(ctx: FlowContext) -> bool:
    """Check if timer is finished"""
    start_time = ctx.get('start_time', 0)
    duration = ctx.get('duration', 5)
    elapsed = time.time() - start_time
    return elapsed >= duration


def example_timer_bot():
    """Bot with polling timer (similar to payment polling)"""
    flow = (
        FlowBuilder("timer_bot")

        .state("start")
            .on_command("/start")
            .reply("⏰ Click to start a 5-second timer!")
            .button("Start Timer", goto="running")

        .state("running")
            .action(start_timer)
            .reply("⏳ Timer started! Waiting 5 seconds...")
            .poll(check_timer_done, interval=1)
            .on_condition(lambda ctx: ctx.poll_result, goto="done")

        .state("done")
            .reply("✅ Timer finished! ⏰")
            .button("Start Again", goto="running")

        .build()
    )

    return flow


# ============================================================================
# Example 5: Conditional Bot (Age Gate)
# ============================================================================

async def check_age_restriction(ctx: FlowContext) -> bool:
    """Check if user is adult (mock implementation)"""
    # In real app, you'd ask user for age
    age = ctx.get('age', 20)
    return age >= 18


def example_age_gate_bot():
    """Bot with conditional flow based on age"""
    flow = (
        FlowBuilder("age_gate_bot")

        .state("start")
            .on_command("/start")
            .reply("🔞 Age Verification\n\nAre you 18 or older?")
            .button("Yes, I'm 18+", callback_data="yes", goto="verify")
            .button("No", callback_data="no", goto="too_young")

        .state("verify")
            .action(lambda ctx: ctx.set('age', 20))  # Mock: set age
            .transition(to="adult_content")

        .state("adult_content")
            .reply("✅ Welcome! You can access this content.")
            .final()

        .state("too_young")
            .reply("❌ Sorry, you must be 18+ to use this bot.")
            .final()

        .build()
    )

    return flow


# ============================================================================
# Visualization Demo
# ============================================================================

def visualize_all_examples():
    """Generate visualizations for all example bots"""
    examples = [
        ("welcome_bot", example_welcome_bot()),
        ("survey_bot", example_survey_bot()),
        ("menu_bot", example_menu_bot()),
        ("timer_bot", example_timer_bot()),
        ("age_gate_bot", example_age_gate_bot()),
    ]

    print("📊 Generating visualizations for all examples...\n")

    for name, flow in examples:
        viz = visualize(flow)

        # Export Mermaid
        viz.export_mermaid(f"docs/examples/{name}.md")

        # Print ASCII for quick view
        print(f"\n{'='*60}")
        print(f"Example: {name}")
        print('='*60)
        print(viz.to_ascii())

    print("\n✅ All visualizations exported to docs/examples/")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run demo"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "visualize":
            # Create examples directory
            os.makedirs("docs/examples", exist_ok=True)
            visualize_all_examples()
            return

        elif sys.argv[1] == "run":
            # Run one of the example bots
            bot_name = sys.argv[2] if len(sys.argv) > 2 else "welcome"

            flows = {
                "welcome": example_welcome_bot(),
                "survey": example_survey_bot(),
                "menu": example_menu_bot(),
                "timer": example_timer_bot(),
                "age_gate": example_age_gate_bot(),
            }

            flow = flows.get(bot_name)
            if not flow:
                print(f"❌ Unknown bot: {bot_name}")
                print(f"Available bots: {', '.join(flows.keys())}")
                return

            # Get bot token
            BOT_TOKEN = os.getenv("BOT_TOKEN")
            if not BOT_TOKEN:
                print("❌ BOT_TOKEN not found in .env!")
                return

            # Run bot
            executor = FlowExecutor(flow, BOT_TOKEN)
            executor.run()
            return

    # Default: show usage
    print("FlowBuilder Examples Demo")
    print("=" * 50)
    print("\nUsage:")
    print("  python demo.py visualize          - Generate all visualizations")
    print("  python demo.py run <bot_name>     - Run example bot")
    print("\nAvailable bots:")
    print("  - welcome    : Simple welcome bot")
    print("  - survey     : Multi-step survey")
    print("  - menu       : Menu navigation")
    print("  - timer      : Polling timer")
    print("  - age_gate   : Conditional flow")
    print("\nExamples:")
    print("  python demo.py visualize")
    print("  python demo.py run menu")


if __name__ == "__main__":
    main()
