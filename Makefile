.PHONY: install install-dev run run-dev test lint format setup clean docker-build docker-run help lock export-requirements venv

# Default target
all: install

# Install project dependencies
install:
	@echo "📦 Installing project dependencies with uv..."
	uv pip install -e .

# Install with dev dependencies
install-dev:
	@echo "📦 Installing project with dev dependencies..."
	uv pip install -e ".[dev]"

# Lock dependencies
lock:
	@echo "🔒 Locking dependencies..."
	uv pip compile pyproject.toml -o requirements.txt

# Export requirements.txt
export-requirements:
	@echo "📄 Exporting requirements.txt..."
	uv pip compile pyproject.toml -o requirements.txt --all-extras

# Create virtual environment
venv:
	@echo "🐍 Creating virtual environment..."
	uv venv

# Run the bot
run:
	@echo "🤖 Starting bot..."
	python run.py

# Run with dev settings
run-dev:
	@echo "🤖 Starting bot in dev mode..."
	python run.py --log-level DEBUG

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest -v

# Run tests with coverage
test-cov:
	@echo "📊 Running tests with coverage..."
	pytest --cov=src --cov-report=html

# Lint code
lint:
	@echo "🔍 Running linting..."
	flake8 src/
	mypy src/

# Format code
format:
	@echo "🎨 Formatting code..."
	black src/
	isort src/

# Setup environment file
setup:
	@echo "⚙️  Setting up environment..."
	@if [ ! -f .env ]; then \
		if [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "✅ Created .env from .env.example"; \
		else \
			echo "❌ No .env.example found"; \
		fi; \
	else \
		echo "✅ .env already exists"; \
	fi

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/ htmlcov/ .coverage .venv

# Build Docker image
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t telegram-knowledge-bot .

# Run with Docker Compose
docker-run:
	@echo "🐳 Starting with Docker Compose..."
	docker-compose up -d

# View logs
docker-logs:
	@echo "📋 Viewing logs..."
	docker-compose logs -f bot

# Stop Docker containers
docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

# Restart Docker containers
docker-restart:
	@echo "🔄 Restarting Docker containers..."
	docker-compose restart

# Check configuration
config-check:
	@echo "✅ Checking configuration..."
	python -c "from src.config import get_settings; settings = get_settings(); print('✅ Configuration loaded'); print(f'Telegram token: {'Set' if settings.telegram.bot_token else 'Missing'}'); print(f'AI provider: {settings.ai.provider}'); print(f'Storage: {settings.storage.primary}')"

# Run setup wizard
setup-wizard:
	@echo "🧙 Running setup wizard..."
	python run.py --setup

# Sync dependencies with uv
sync:
	@echo "🔄 Syncing dependencies..."
	uv sync

# Update all dependencies
update:
	@echo "⬆️  Updating all dependencies..."
	uv pip install --upgrade -e ".[dev]"

# Lock dependencies to requirements.txt
lock:
	@echo "🔒 Locking dependencies to requirements.txt..."
	uv pip compile pyproject.toml -o requirements.txt

# Create lock file with uv
lock-uv:
	@echo "🔒 Creating uv.lock file..."
	uv lock

# Help
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies using uv"
	@echo "  make install-dev  - Install with dev dependencies"
	@echo "  make run          - Run the bot"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make setup        - Setup .env file"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker-run   - Run with Docker Compose"
	@echo "  make lock         - Lock dependencies to requirements.txt"
	@echo "  make sync         - Sync dependencies with uv"
	@echo "  make help         - Show this help"