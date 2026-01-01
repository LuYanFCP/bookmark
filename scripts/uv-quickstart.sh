#!/bin/bash
# Quick setup script using uv

echo "🤖 Telegram Knowledge Bot - Quick Setup with uv"
echo "=============================================="
echo ""

# Install uv if not exists
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv pip install -e ".[dev]"

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📄 Creating .env file..."
    cat > .env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI Configuration (OpenAI)
OPENAI_API_KEY=your_openai_api_key_here

# Storage (Optional - Uncomment to use)
# NOTION_API_KEY=your_notion_api_key_here
# NOTION_DATABASE_ID=your_notion_database_id_here
# OBSIDIAN_VAULT_PATH=/path/to/your/vault
EOF
fi

echo ""
echo "✅ Setup complete! Edit .env and run: python run.py"