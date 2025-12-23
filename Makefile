.PHONY: install install-dev test test-cov lint format typecheck clean help

# Default target
help:
	@echo "Market Data Pipeline - Available Commands"
	@echo ""
	@echo "  make install      Install package"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Run linter (ruff)"
	@echo "  make format       Format code (ruff)"
	@echo "  make typecheck    Run type checker (mypy)"
	@echo "  make clean        Remove build artifacts"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src/market_data --cov-report=term-missing

test-fast:
	pytest tests/ -v --ignore=tests/integration

# Code Quality
lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Development
dev:
	pip install -e ".[dev]" && pre-commit install
