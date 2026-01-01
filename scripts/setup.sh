#!/bin/bash
# Setup script for Telegram Knowledge Bot
# This script helps with initial setup using uv

set -e

echo "🤖 Telegram Knowledge Bot Setup"
echo "=============================="

echo ""
echo "📚 Installing Dependencies with uv..."
echo ""

# Install dependencies
echo "📦 Installing project dependencies..."
uv pip install -e ".[dev]"

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "⚠️  REMEMBER: You must manually create a .env file!"
echo ""
echo "📋 Steps:"
echo "   1. Copy .env.example to .env"
echo "   2. Fill in your API keys and tokens"
echo "   3. Run: python run.py"
echo ""
echo "📝 Required:"
echo "   • TELEGRAM_BOT_TOKEN (from @BotFather)"
echo "   • OPENAI_API_KEY (from OpenAI platform)"
echo "   • NOTION_API_KEY & NOTION_DATABASE_ID (optional)"
echo "   • OBSIDIAN_VAULT_PATH (optional)"