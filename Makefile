# Makefile for MeetPing-Pay project

.PHONY: help run run-flow test visualize status clean

help:
	@python main.py help

run:
	@python main.py payment

run-flow:
	@python main.py payment-flow

agent:
	@python main.py agent

mcp-test:
	@python main.py mcp-test

test:
	@pytest tests/ -v

test-cov:
	@pytest tests/ --cov=. --cov-report=html

visualize:
	@python main.py visualize

status:
	@python main.py status

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✨ Cleaned up Python cache files"
