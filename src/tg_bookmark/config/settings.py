"""Application settings and configuration management."""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIConfig(BaseSettings):
    """AI provider configuration."""

    provider: str = Field(default="openai", validation_alias="AI_PROVIDER")
    
    # OpenAI LLM settings
    openai_endpoint: str | None = Field(default=None, validation_alias="OPENAI_ENDPOINT")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="openai_model")
    
    # OpenAI Embedding settings (separate provider)
    openai_embedding_endpoint: str | None = Field(default=None, validation_alias="OPENAI_EMBEDDING_ENDPOINT")
    openai_embedding_api_key: str | None = Field(default=None, validation_alias="OPENAI_EMBEDDING_API_KEY")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", validation_alias="OPENAI_EMBEDDING_MODEL"
    )
    
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-haiku-20240307", validation_alias="ANTHROPIC_MODEL"
    )


class TelegramConfig(BaseSettings):
    """Telegram bot configuration."""

    bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    admin_users: List[int] = Field(default_factory=list, validation_alias="TELEGRAM_ADMIN_USERS")
    allowed_chats: List[int] = Field(default_factory=list, validation_alias="TELEGRAM_ALLOWED_CHATS")

    @property
    def admin_users_list(self) -> List[int]:
        """Parse admin users from comma-separated string."""
        if isinstance(self.admin_users, str):
            return [
                int(uid.strip()) for uid in self.admin_users.split(",") if uid.strip()
            ]
        return self.admin_users

    @property
    def allowed_chats_list(self) -> List[int]:
        """Parse allowed chats from comma-separated string."""
        if isinstance(self.allowed_chats, str):
            return [
                int(cid.strip()) for cid in self.allowed_chats.split(",") if cid.strip()
            ]
        return self.allowed_chats


class NotionConfig(BaseSettings):
    """Notion storage configuration."""

    api_key: Optional[str] = Field(default=None, validation_alias="NOTION_API_KEY")
    database_id: Optional[str] = Field(default=None, validation_alias="NOTION_DATABASE_ID")

    @property
    def is_enabled(self) -> bool:
        """Check if Notion storage is enabled."""
        return bool(self.api_key and self.database_id)


class ObsidianConfig(BaseSettings):
    """Obsidian storage configuration."""

    vault_path: Optional[str] = Field(default=None, validation_alias="OBSIDIAN_VAULT_PATH")
    daily_notes: bool = Field(default=True, validation_alias="OBSIDIAN_DAILY_NOTES")
    folder_structure: str = Field(
        default="Inbox/{category}", validation_alias="OBSIDIAN_FOLDER_STRUCTURE"
    )

    @property
    def is_enabled(self) -> bool:
        """Check if Obsidian storage is enabled."""
        return bool(self.vault_path and os.path.exists(self.vault_path))


class StorageConfig(BaseSettings):
    """Storage configuration."""

    primary: str = Field(default="notion", validation_alias="STORAGE_PRIMARY")
    notion: NotionConfig = Field(default_factory=NotionConfig)
    obsidian: ObsidianConfig = Field(default_factory=ObsidianConfig)


class ProcessingConfig(BaseSettings):
    """Processing and queue configuration."""

    queue_backend: str = Field(default="redis", validation_alias="QUEUE_BACKEND")
    redis_url: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")
    concurrency: int = Field(default=3, validation_alias="WORKER_CONCURRENCY")
    timeout: int = Field(default=300, validation_alias="PROCESSING_TIMEOUT")


class FeaturesConfig(BaseSettings):
    """Feature flags configuration."""

    auto_summarize: bool = Field(default=True, validation_alias="FEATURE_AUTO_SUMMARIZE")
    auto_classify: bool = Field(default=True, validation_alias="FEATURE_AUTO_CLASSIFY")
    smart_reply: bool = Field(default=True, validation_alias="FEATURE_SMART_REPLY")
    content_extraction: bool = Field(default=True, validation_alias="FEATURE_CONTENT_EXTRACTION")
    ocr_enabled: bool = Field(default=True, validation_alias="FEATURE_OCR_ENABLED")


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    format: str = Field(default="json", validation_alias="LOG_FORMAT")
    # Removed: Sentry DSN configuration (no longer supported)


class Settings(BaseSettings):
    """Main application settings."""

    ai: AIConfig = Field(default_factory=AIConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')



# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
