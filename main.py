#!/usr/bin/env python3
"""
Main entry point for MeetPing-Pay bots.
Run different bots or utilities via CLI arguments.
"""
import sys
import asyncio
from config import config


def print_usage():
    """Print usage information"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║              MeetPing-Pay Bot Runner                           ║
╚════════════════════════════════════════════════════════════════╝

Usage:
    python main.py [command]

Commands:
    payment         Run payment bot (declarative flow version) [DEFAULT]
    agent           Run homework agent example
    mcp-test        Run MCP test agent
    visualize       Generate payment flow diagram
    status          Show configuration status
    help            Show this help message

Examples:
    python main.py                 # Run payment bot (default)
    python main.py visualize       # Generate flow diagrams
    python main.py status          # Check configuration
    python main.py agent           # Run homework agent
""")


def run_payment_bot():
    """Run payment bot (declarative flow version)"""
    print("🤖 Starting Payment Bot...")
    from bot_flow.flows.payment_flow import main as payment_main
    payment_main()


async def run_agent():
    """Run homework agent example"""
    print("🤖 Starting Homework Agent...")
    from agent import main as agent_main
    await agent_main()


def run_mcp_test():
    """Run MCP test agent"""
    print("🤖 Starting MCP Test Agent...")
    from mcp_test import main as mcp_main
    mcp_main()


def run_visualize():
    """Generate flow visualization"""
    print("📊 Generating flow visualization...")
    from visualize_payment_flow import main as viz_main
    viz_main()


def show_status():
    """Show configuration status"""
    config.print_status()


def main():
    """Main entry point"""
    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "payment"

    # Handle help first (no validation needed)
    if command == "help":
        print_usage()
        return

    # Show status
    if command == "status":
        show_status()
        return

    # Validate config for bot commands
    if not config.validate():
        print("\n💡 Tip: Add BOT_TOKEN to your .env file")
        sys.exit(1)

    # Command handlers
    commands = {
        "payment": run_payment_bot,
        "agent": lambda: asyncio.run(run_agent()),
        "mcp-test": run_mcp_test,
        "visualize": run_visualize,
    }

    handler = commands.get(command)

    if not handler:
        print(f"❌ Unknown command: {command}\n")
        print_usage()
        sys.exit(1)

    # Show config status before running
    if command not in ["visualize"]:
        config.print_status()
        print()

    # Run command
    handler()


if __name__ == "__main__":
    main()
