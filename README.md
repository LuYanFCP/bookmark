# Telegram Knowledge Bot 🤖

An AI-powered Telegram bot that automatically processes, summarizes, classifies, and stores your messages to Notion and/or Obsidian.

## Features

- 🤖 **AI-Powered Processing**
  - Intelligent message summarization
  - Automatic category classification
  - Smart keyword extraction
  - Text embeddings for semantic search
- 📥 **Multi-Modal Support**
  - Text messages
  - Documents (PDF, DOC, DOCX, TXT)
  - Photos (with OCR)
  - URLs (automatic content extraction)
- 🗄️ **Multiple Storage Options**
  - Notion database integration
  - Obsidian vault integration
  - Support for both simultaneously
- 🎛️ **Flexible Configuration**
  - Multiple AI providers (OpenAI, Anthropic)
  - Feature flags for customization
  - Rate limiting and error handling

## Architecture

```
Telegram API → Bot → Message Queue → AI Processing → Storage
                      ↓                ↓              ↓
                  Content Extraction  Summary     Notion/Obsidian
                      (URLs, OCR)    Category      
```

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Telegram Bot Token (from @BotFather)
- OpenAI API Key (or Anthropic)
- Notion Database (optional)
- Obsidian Vault (optional)

### 2. Installation

```bash
# Clone repository
git clone <repository-url>
cd telegram-knowledge-bot

# Install using uv (recommended)
uv pip install -e .

# Or with dev dependencies
uv pip install -e ".[dev]"

# Or using pip
pip install -r requirements.txt
```

### 3. Configuration

#### Create .env File

Create a `.env` file with your configuration:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_notion_database_id_here
OBSIDIAN_VAULT_PATH=/path/to/your/vault
```

Or use the interactive setup wizard:

```bash
python run.py --setup
```

#### Validate Configuration

Check if your configuration is valid:

```bash
python run.py --check
```

### 4. Run the Bot

```bash
# Polling mode (default)
python run.py

# Webhook mode
python run.py --mode webhook --port 8443

# With custom environment file
python run.py --env-file .env.production
```

### 5. Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot
```

## Configuration Options

### Environment Variables

#### Telegram
- `TELEGRAM_BOT_TOKEN`: Your bot token (required)
- `TELEGRAM_ADMIN_USERS`: Comma-separated list of admin user IDs
- `TELEGRAM_ALLOWED_CHATS`: Comma-separated list of allowed chat IDs

#### AI Provider
- `AI_PROVIDER`: "openai" or "anthropic" (default: openai)
- `OPENAI_API_KEY`: OpenAI API key
- `OPENAI_MODEL`: GPT model (default: gpt-4o-mini)
- `ANTHROPIC_API_KEY`: Anthropic API key

#### Storage
- `STORAGE_PRIMARY`: "notion" or "obsidian" (default: notion)
- `NOTION_API_KEY`: Notion API key
- `NOTION_DATABASE_ID`: Notion database ID
- `OBSIDIAN_VAULT_PATH`: Path to Obsidian vault

#### Features
- `FEATURE_AUTO_SUMMARIZE`: Enable auto-summarization (default: true)
- `FEATURE_AUTO_CLASSIFY`: Enable auto-classification (default: true)
- `FEATURE_OCR_ENABLED`: Enable OCR for images (default: true)

#### Logging
- `LOG_LEVEL`: Log level with options (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Default: `INFO`
  - `DEBUG`: Detailed debug information (use for development)
  - `INFO`: Important business events (default, recommended for production)
  - `WARNING`: Warning messages only
  - `ERROR`: Error messages only
  
**Note:** Logs are output to console only in structured **logfmt** format.

**Example:**
```bash
# Development mode with detailed logs
LOG_LEVEL=DEBUG python run.py

# Production mode with standard logs
LOG_LEVEL=INFO python run.py

# View all available configuration parameters
python run.py --show-config
```

## Usage with Make and uv

```bash
# Install dependencies
make install

# Install with dev tools
make install-dev

# Run the bot
make run

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Clean generated files
make clean

# Docker operations
make docker-build
make docker-run
make docker-logs
make docker-stop
```

## Usage

### Commands

- `/start` - Start the bot and show welcome message
- `/help` - Show help information
- `/settings` - View bot settings
- `/stats` - View your statistics
- `/export` - Export your data

### Message Processing

Simply send any message to the bot:

1. **Text Messages**: Automatically summarized and classified
2. **Documents**: Content extracted and processed
3. **Photos**: OCR text extraction
4. **URLs**: Content fetched and summarized

The bot will respond with:
- Category and tags
- AI-generated summary
- Processing statistics

### Notion Database Setup

1. Create a new Notion database
2. Add these properties:
   - Title (Title)
   - Category (Select)
   - Tags (Multi-select)
   - User ID (Number)
   - Message ID (Number)
   - Date (Date)
   - Keywords (Multi-select)

3. Share database with your Notion integration
4. Copy database ID from the URL

### Obsidian Setup

1. Set `OBSIDIAN_VAULT_PATH` to your vault location
2. Configure folder structure (default: `Inbox/{category}`)
3. Enable/disable daily notes

## Development

### Using uv for Development

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install in editable mode
uv pip install -e ".[dev]"

# Lock dependencies
uv pip compile pyproject.toml -o requirements.txt
```

### Project Structure

```
src/
├── telegram_bot/          # Bot logic
│   ├── handlers/          # Message handlers
│   ├── middleware/        # Middleware components
│   └── bot.py            # Main bot class
├── ai_engine/            # AI processing
│   ├── summarizer.py     # Message summarization
│   ├── classifier.py     # Content classification
│   └── providers.py      # AI provider adapters
├── storage/              # Storage implementations
│   ├── notion.py         # Notion adapter
│   ├── obsidian.py       # Obsidian adapter
│   └── base.py           # Base storage interface
├── content_extractor/    # Content extraction
│   ├── pipeline.py       # Extraction pipeline
│   ├── url_processor.py  # URL processing
│   ├── file_processor.py # File processing
│   └── ocr.py           # OCR functionality
└── config/               # Configuration
    └── settings.py       # Settings management
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_summarizer.py
```

## Docker Deployment

### Production with Docker Compose

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - NOTION_API_KEY=${NOTION_API_KEY}
      - NOTION_DATABASE_ID=${NOTION_DATABASE_ID}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Deploy:

```bash
# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Deploy
docker-compose -f docker-compose.production.yml up -d
```

## Troubleshooting

### Common Issues

**Bot not responding**
- Check TELEGRAM_BOT_TOKEN is correct
- Verify bot is not in privacy mode (disable with @BotFather)

**AI processing fails**
- Verify OPENAI_API_KEY is valid
- Check API rate limits
- Review error logs

**Notion storage fails**
- Confirm database ID is correct
- Check Notion API key permissions
- Verify database has required properties

**Obsidian storage fails**
- Check vault path exists
- Verify write permissions
- Check disk space

### Debug Mode

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

View detailed logs:

```bash
docker-compose logs -f bot | grep DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Create an issue for bugs
- Start a discussion for feature requests
- Check wiki for advanced usage

## Using uv (Recommended)

This project uses `uv` as the primary package manager for its speed and reliability.

### Installing uv

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Basic uv Commands

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Lock dependencies
uv pip compile pyproject.toml -o requirements.txt

# Sync dependencies (uv-specific)
uv sync

# Update dependencies
uv pip install --upgrade -e ".[dev]"
```

For more information about uv, visit: https://github.com/astral-sh/uv
