#!/bin/bash
# MeetPing-Pay Bot Runner
# Convenient script to run different bot implementations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file with BOT_TOKEN and other required variables."
    exit 1
fi

# Function to display usage
usage() {
    echo -e "${GREEN}MeetPing-Pay Bot Runner${NC}"
    echo ""
    echo "Usage: ./run_bot.sh [command]"
    echo ""
    echo "Commands:"
    echo "  original          - Run original imperative payment_bot.py"
    echo "  flow              - Run declarative bot_flow payment bot"
    echo "  demo [bot_name]   - Run bot_flow example bot"
    echo "  visualize         - Generate all flow visualizations"
    echo "  test              - Run all tests"
    echo ""
    echo "Examples:"
    echo "  ./run_bot.sh original              # Run payment_bot.py"
    echo "  ./run_bot.sh flow                  # Run declarative flow bot"
    echo "  ./run_bot.sh demo menu             # Run menu example"
    echo "  ./run_bot.sh visualize             # Generate diagrams"
    echo ""
    exit 0
}

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 not found!${NC}"
        exit 1
    fi
}

# Run original imperative bot
run_original() {
    echo -e "${GREEN}Starting original payment_bot.py...${NC}"
    python3 payment_bot.py
}

# Run declarative flow bot
run_flow() {
    echo -e "${GREEN}Starting declarative bot_flow payment bot...${NC}"
    python3 bot_flow/flows/payment_flow.py
}

# Run demo bot
run_demo() {
    local bot_name=${1:-welcome}
    echo -e "${GREEN}Starting demo bot: ${bot_name}${NC}"
    python3 bot_flow/examples/demo.py run "$bot_name"
}

# Generate visualizations
run_visualize() {
    echo -e "${GREEN}Generating flow visualizations...${NC}"

    # Payment flow
    echo -e "${YELLOW}→ Generating payment_flow diagrams...${NC}"
    python3 visualize_payment_flow.py

    # Demo flows
    echo -e "${YELLOW}→ Generating demo bot diagrams...${NC}"
    python3 bot_flow/examples/demo.py visualize

    echo -e "${GREEN}✓ All visualizations generated!${NC}"
    echo ""
    echo "Generated files:"
    echo "  - docs/payment_flow.md (Mermaid)"
    echo "  - docs/payment_flow.dot (GraphViz)"
    echo "  - docs/payment_flow.txt (ASCII)"
    echo "  - docs/examples/*.md (Demo bots)"
}

# Run tests
run_tests() {
    echo -e "${GREEN}Running tests...${NC}"

    # Unit tests
    echo -e "${YELLOW}→ Running unit tests...${NC}"
    pytest test_payment_bot.py -v

    # Integration tests (if .env.test exists)
    if [ -f .env.test ]; then
        echo -e "${YELLOW}→ Running integration tests...${NC}"
        pytest test_integration_nocodb.py -v
    else
        echo -e "${YELLOW}⚠ Skipping integration tests (.env.test not found)${NC}"
    fi

    echo -e "${GREEN}✓ Tests completed!${NC}"
}

# Main script
check_python

case "${1:-}" in
    original)
        run_original
        ;;
    flow)
        run_flow
        ;;
    demo)
        run_demo "$2"
        ;;
    visualize)
        run_visualize
        ;;
    test)
        run_tests
        ;;
    -h|--help|help|"")
        usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '${1}'${NC}"
        echo ""
        usage
        ;;
esac
