.PHONY: help install dev run test lint format clean docs

help:
	@echo "LingoLearn API - Available Commands"
	@echo "===================================="
	@echo "  make install    - Install dependencies with uv"
	@echo "  make dev        - Run development server"
	@echo "  make run        - Run production server"
	@echo "  make test       - Run tests with pytest"
	@echo "  make test-cov   - Run tests with coverage"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Remove cache and build files"
	@echo "  make docs       - Open API documentation"

install:
	@echo "📦 Installing dependencies..."
	uv sync

dev:
	@echo "🚀 Starting development server..."
	uv run uvicorn src.main:app --host 127.0.0.1 --port 1234 --reload

run:
	@echo "🚀 Starting production server..."
	uv run uvicorn src.main:app --host 0.0.0.0 --port 1234

test:
	@echo "🧪 Running tests..."
	uv run pytest -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run pytest --cov=. --cov-report=html --cov-report=term

lint:
	@echo "🔍 Running linting checks..."
	uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	uv run black --check .

format:
	@echo "✨ Formatting code..."
	uv run black .
	uv run isort .

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

docs:
	@echo "📚 Opening API documentation..."
	@python -m webbrowser "http://127.0.0.1:1234/docs"

.DEFAULT_GOAL := help
