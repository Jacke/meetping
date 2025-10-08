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
    echo "  install           - Install Python dependencies"
    echo "  original          - Run original imperative payment_bot.py"
    echo "  flow              - Run declarative bot_flow payment bot"
    echo "  demo [bot_name]   - Run bot_flow example bot"
    echo "  visualize         - Generate all flow visualizations"
    echo "  test              - Run all tests"
    echo ""
    echo "Examples:"
    echo "  ./run_bot.sh install               # Install dependencies"
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

# Install dependencies
run_install() {
    echo -e "${GREEN}Installing Python dependencies...${NC}"

    if [ ! -f requirements.txt ]; then
        echo -e "${RED}Error: requirements.txt not found!${NC}"
        exit 1
    fi

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv .venv
    fi

    # Activate venv and install
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
    pip install -r requirements.txt

    echo -e "${GREEN}✓ Dependencies installed in .venv!${NC}"
    echo -e "${YELLOW}Note: Commands will automatically use .venv${NC}"
}

# Run original imperative bot
run_original() {
    echo -e "${GREEN}Starting original payment_bot.py...${NC}"
    if [ -f ".venv/bin/python" ]; then
        .venv/bin/python payment_bot.py
    else
        python3 payment_bot.py
    fi
}

# Run declarative flow bot
run_flow() {
    echo -e "${GREEN}Starting declarative bot_flow payment bot...${NC}"
    if [ -f ".venv/bin/python" ]; then
        PYTHONPATH=. .venv/bin/python bot_flow/flows/payment_flow.py
    else
        PYTHONPATH=. python3 bot_flow/flows/payment_flow.py
    fi
}

# Run demo bot
run_demo() {
    local bot_name=${1:-welcome}
    echo -e "${GREEN}Starting demo bot: ${bot_name}${NC}"
    if [ -f ".venv/bin/python" ]; then
        PYTHONPATH=. .venv/bin/python bot_flow/examples/demo.py run "$bot_name"
    else
        PYTHONPATH=. python3 bot_flow/examples/demo.py run "$bot_name"
    fi
}

# Generate visualizations
run_visualize() {
    echo -e "${GREEN}Generating flow visualizations...${NC}"

    # Payment flow
    echo -e "${YELLOW}→ Generating payment_flow diagrams...${NC}"
    PYTHONPATH=. python3 visualize_payment_flow.py

    # Demo flows (skip if dependencies not installed)
    echo -e "${YELLOW}→ Generating demo bot diagrams...${NC}"
    if PYTHONPATH=. python3 -c "import telegram" 2>/dev/null; then
        PYTHONPATH=. python3 bot_flow/examples/demo.py visualize
    else
        echo -e "${YELLOW}⚠ Skipping demo visualizations (run 'pip install -r requirements.txt' first)${NC}"
    fi

    echo -e "${GREEN}✓ Visualizations generated!${NC}"
    echo ""
    echo "Generated files:"
    echo "  - docs/payment_flow.md (Mermaid)"
    echo "  - docs/payment_flow.dot (GraphViz)"
    echo "  - docs/payment_flow.txt (ASCII)"
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
    install)
        run_install
        ;;
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
