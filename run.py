#!/usr/bin/env python3
"""
Telegram Knowledge Bot - Main entry point using uv

This bot processes Telegram messages with AI-powered summarization,
classification, and stores them in Notion/Obsidian.

Uses uv for fast Python package management: https://github.com/astral-sh/uv
"""

import argparse
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tg_bookmark.telegram_bot import KnowledgeBot
from tg_bookmark.config import get_settings


def check_uv():
    """Check if uv is installed and working."""
    try:
        import subprocess
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass

    print("⚠️  uv not found. Consider installing uv for faster dependency management:")
    print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Telegram Knowledge Bot - AI-powered message processing and storage"
    )

    parser.add_argument(
        "--mode",
        choices=["polling", "webhook"],
        default="polling",
        help="Bot run mode (default: polling)"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Webhook host (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8443,
        help="Webhook port (default: 8443)"
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to environment file"
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run setup wizard"
    )

    parser.add_argument(
        "--install",
        action="store_true",
        help="Install dependencies using uv"
    )

    parser.add_argument(
        "--install-dev",
        action="store_true",
        help="Install dependencies with dev tools"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check configuration and dependencies"
    )

    return parser.parse_args()


def install_dependencies(dev=False):
    """Install dependencies using uv."""
    import subprocess

    print("📦 Installing dependencies with uv...")

    try:
        if dev:
            cmd = ["uv", "pip", "install", "-e", ".[dev]"]
        else:
            cmd = ["uv", "pip", "install", "-e", "."]

        result = subprocess.run(cmd, check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("❌ uv not found. Please install uv first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False


def run_setup():
    """Interactive setup wizard."""
    print("🧙 Telegram Knowledge Bot - Setup Wizard")
    print("=" * 50)

    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📄 Creating .env file...")

        # Copy example file
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ Created .env file from .env.example")
        else:
            # Create basic .env file
            env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# AI Provider Configuration (OpenAI or Anthropic)
OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Notion Configuration (Optional)
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_notion_database_id_here

# Obsidian Configuration (Optional)
OBSIDIAN_VAULT_PATH=/path/to/your/vault
"""
            env_file.write_text(env_content)
            print("✅ Created basic .env file")
    else:
        print("✅ .env file already exists")

    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("❌ Setup incomplete due to dependency installation failure")
        return False

    print("\n✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Edit .env file with your API keys and tokens")
    print("   2. Run: python run.py")
    print("\n📝 Required credentials:")
    print("   - TELEGRAM_BOT_TOKEN: Get from @BotFather on Telegram")
    print("   - OPENAI_API_KEY: Get from https://platform.openai.com")
    print("   - NOTION_API_KEY and NOTION_DATABASE_ID: Optional, for Notion storage")
    print("   - OBSIDIAN_VAULT_PATH: Optional, for Obsidian storage")

    return True


def validate_config():
    """Validate configuration before starting."""
    settings = get_settings()
    errors = []
    warnings = []

    # Check critical requirements
    if not settings.telegram.bot_token:
        errors.append("TELEGRAM_BOT_TOKEN is not set")

    if not settings.ai.openai_api_key and not settings.ai.anthropic_api_key:
        errors.append("Either OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")

    # Check storage configuration
    if settings.storage.primary == "notion":
        if not settings.storage.notion.is_enabled:
            warnings.append("Notion is set as primary storage but NOTION_API_KEY or NOTION_DATABASE_ID is missing")
    elif settings.storage.primary == "obsidian":
        if not settings.storage.obsidian.is_enabled:
            warnings.append("Obsidian is set as primary storage but OBSIDIAN_VAULT_PATH is missing or invalid")

    # Check optional features
    if not settings.storage.notion.is_enabled and not settings.storage.obsidian.is_enabled:
        warnings.append("No storage is configured. The bot will only process and display results, not save them.")

    # Report issues
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease check your .env file")
        return False

    if warnings:
        print("⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"   - {warning}")
        print("\nContinue anyway? [y/N]: ", end="")
        response = input()
        if response.lower() != 'y':
            return False

    print("✅ Configuration validated successfully")
    print(f"   AI Provider: {settings.ai.provider}")
    print(f"   Storage: {settings.storage.primary}")
    print(f"   Notion: {'Enabled' if settings.storage.notion.is_enabled else 'Disabled'}")
    print(f"   Obsidian: {'Enabled' if settings.storage.obsidian.is_enabled else 'Disabled'}")

    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")

    missing_deps = []

    try:
        import telegram
        print(f"✅ python-telegram-bot: {telegram.__version__}")
    except ImportError:
        missing_deps.append("python-telegram-bot")

    try:
        import openai
        print(f"✅ openai: {openai.__version__}")
    except ImportError:
        missing_deps.append("openai")

    try:
        import pydantic
        print(f"✅ pydantic: {pydantic.__version__}")
    except ImportError:
        missing_deps.append("pydantic")

    try:
        import notion_client
        print("✅ notion-client")
    except ImportError:
        print("⚠️  notion-client (optional, for Notion storage)")

    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Run 'python run.py --install' to install them")
        return False

    print("\n✅ All required dependencies are installed")
    return True


def main():
    """Main entry point."""
    args = parse_args()

    # Handle uv installation check
    check_uv()

    # Handle installation
    if args.install:
        if install_dependencies(dev=False):
            print("\n✅ Dependencies installed successfully")
            sys.exit(0)
        else:
            sys.exit(1)

    if args.install_dev:
        if install_dependencies(dev=True):
            print("\n✅ Dependencies with dev tools installed successfully")
            sys.exit(0)
        else:
            sys.exit(1)

    # Run setup wizard
    if args.setup:
        if run_setup():
            sys.exit(0)
        else:
            sys.exit(1)

    # Check configuration and dependencies
    if args.check:
        print("🔍 Running pre-flight checks...\n")
        config_ok = validate_config()
        deps_ok = check_dependencies()
        sys.exit(0 if (config_ok and deps_ok) else 1)

    # Validate before running
    print("🔍 Running pre-flight checks...\n")
    if not validate_config() or not check_dependencies():
        print("\n❌ Cannot start bot. Please fix the issues above.")
        print("Run 'python run.py --help' for assistance.")
        sys.exit(1)

    print("\n🚀 Starting Telegram Knowledge Bot...\n")
    print(f"   Mode: {args.mode}")
    print(f"   AI Provider: {get_settings().ai.provider}")
    print(
        f"   Storage: {get_settings().storage.primary} "
        f"(Notion: {'✅' if get_settings().storage.notion.is_enabled else '❌'}, "
        f"Obsidian: {'✅' if get_settings().storage.obsidian.is_enabled else '❌'})"
    )
    print("")

    # Create and run bot
    bot = KnowledgeBot()

    try:
        if args.mode == "polling":
            print("🤖 Starting polling (press Ctrl+C to stop)...")
            bot.run(mode="polling")
        else:
            print(f"🤖 Starting webhook on {args.host}:{args.port}...")
            bot.run(mode="webhook", host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error in {args.mode} mode: {e}")
        print("                   ")
        print("🔍 Full error details:")
        print("─" * 70)
        traceback.print_exc()
        print("─" * 70)
        print("                   ")
        print("💡 Tip: Run with --check to validate your configuration")
        print("🔗 For help: See README.md or check logs/")
        sys.exit(1)


if __name__ == "__main__":
    main()
