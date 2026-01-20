"""
Comprehensive example: FastAPI application with ConfigPlusPlus

This example demonstrates:
1. Environment-based configuration for secrets and infrastructure
2. YAML-based configuration for application features
3. Configuration validation
4. Pretty configuration display
5. Integration with LoggerPlusPlus
"""

import pathlib
import sys
from typing import List
from dataclasses import dataclass

from configplusplus import EnvConfigLoader, YamlConfigLoader, env, safe_load_envs
from loggerplusplus import loggerplusplus
from loggerplusplus import formats as lpp_formats

# ============================================================================
# Environment-based Configuration (Secrets & Infrastructure)
# ============================================================================

safe_load_envs(".env")


class InfraConfig(EnvConfigLoader):
    """Infrastructure configuration from environment variables."""

    # ──── Application ────
    APP_NAME = env("APP_NAME", default="Document Search API")
    APP_VERSION = env("APP_VERSION", default="1.0.0")
    ENVIRONMENT = env("ENVIRONMENT", default="development")

    # ──── Server ────
    HOST = env("HOST", default="0.0.0.0")
    PORT = env("PORT", cast=int, default=8000)
    WORKERS = env("WORKERS", cast=int, default=4)

    # ──── Database ────
    DATABASE_HOST = env("DATABASE_HOST", default="localhost")
    DATABASE_PORT = env("DATABASE_PORT", cast=int, default=5432)
    DATABASE_NAME = env("DATABASE_NAME")
    DATABASE_USER = env("DATABASE_USER")
    DATABASE_PASSWORD = env("DATABASE_PASSWORD")  # Will be masked
    DATABASE_POOL_SIZE = env("DATABASE_POOL_SIZE", cast=int, default=10)
    DATABASE_MAX_OVERFLOW = env("DATABASE_MAX_OVERFLOW", cast=int, default=20)

    # ──── Redis ────
    REDIS_HOST = env("REDIS_HOST", default="localhost")
    REDIS_PORT = env("REDIS_PORT", cast=int, default=6379)
    REDIS_DB = env("REDIS_DB", cast=int, default=0)
    REDIS_PASSWORD = env("REDIS_PASSWORD", required=False)  # Optional

    # ──── Qdrant Vector Database ────
    QDRANT_URL = env("QDRANT_URL", default="http://localhost:6333")
    QDRANT_COLLECTION = env("QDRANT_COLLECTION", default="documents")

    # ──── OpenAI ────
    SECRET_OPENAI_API_KEY = env("SECRET_OPENAI_API_KEY")  # Will be masked
    OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4")
    OPENAI_EMBEDDING_MODEL = env(
        "OPENAI_EMBEDDING_MODEL", default="text-embedding-ada-002"
    )
    OPENAI_TEMPERATURE = env("OPENAI_TEMPERATURE", cast=float, default=0.7)
    OPENAI_MAX_TOKENS = env("OPENAI_MAX_TOKENS", cast=int, default=4000)

    # ──── Security ────
    SECRET_JWT_KEY = env("SECRET_JWT_KEY")  # Will be masked
    JWT_ALGORITHM = env("JWT_ALGORITHM", default="HS256")
    TOKEN_EXPIRE_MINUTES = env("TOKEN_EXPIRE_MINUTES", cast=int, default=60)

    # ──── Features ────
    ENABLE_CORS = env("ENABLE_CORS", cast=bool, default=True)
    ENABLE_DOCS = env("ENABLE_DOCS", cast=bool, default=False)
    ENABLE_METRICS = env("ENABLE_METRICS", cast=bool, default=True)

    # ──── Logging ────
    LOG_LEVEL = env("LOG_LEVEL", default="INFO")
    LOG_FILE = env("LOG_FILE", cast=pathlib.Path, required=False)

    # ──── Paths ────
    DATA_DIR = env("DATA_DIR", cast=pathlib.Path, default=pathlib.Path("./data"))
    UPLOAD_DIR = env("UPLOAD_DIR", cast=pathlib.Path, default=pathlib.Path("./uploads"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        super().validate()

        # Validate ports
        if not 1024 <= cls.PORT <= 65535:
            raise RuntimeError("PORT must be between 1024 and 65535")

        if not 1024 <= cls.DATABASE_PORT <= 65535:
            raise RuntimeError("DATABASE_PORT must be between 1024 and 65535")

        # Validate workers
        if cls.WORKERS < 1:
            raise RuntimeError("WORKERS must be at least 1")

        # Validate OpenAI settings
        if not 0 <= cls.OPENAI_TEMPERATURE <= 2:
            raise RuntimeError("OPENAI_TEMPERATURE must be between 0 and 2")

        # Validate directories
        if not cls.DATA_DIR.exists():
            cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

        if not cls.UPLOAD_DIR.exists():
            cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_database_url(cls) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{cls.DATABASE_USER}:{cls.DATABASE_PASSWORD}"
            f"@{cls.DATABASE_HOST}:{cls.DATABASE_PORT}/{cls.DATABASE_NAME}"
        )

    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL."""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"


# ============================================================================
# YAML-based Configuration (Application Features)
# ============================================================================


@dataclass
class FilterConfig:
    """Configuration for a search filter."""

    name: str
    type: str
    label: str
    enabled: bool = True
    values: List[str] = None


@dataclass
class ProcessorConfig:
    """Configuration for a document processor."""

    name: str
    enabled: bool
    priority: int
    extensions: List[str]
    max_size_mb: int = 50


class AppConfig(YamlConfigLoader):
    """Application-specific configuration from YAML."""

    def __post_init__(self) -> None:
        """Parse YAML configuration."""

        # Parse search filters
        self.filters: List[FilterConfig] = [
            FilterConfig(**f) for f in self._raw_config.get("filters", [])
        ]

        # Parse document processors
        self.processors: List[ProcessorConfig] = [
            ProcessorConfig(**p) for p in self._raw_config.get("processors", [])
        ]

        # Parse UI settings
        ui_config = self._raw_config.get("ui", {})
        self.theme = ui_config.get("theme", "light")
        self.items_per_page = ui_config.get("items_per_page", 10)
        self.enable_preview = ui_config.get("enable_preview", True)

        # Parse search settings
        search_config = self._raw_config.get("search", {})
        self.max_results = search_config.get("max_results", 100)
        self.highlight_terms = search_config.get("highlight_terms", True)
        self.fuzzy_matching = search_config.get("fuzzy_matching", False)

    def get_enabled_filters(self) -> List[FilterConfig]:
        """Get list of enabled filters."""
        return [f for f in self.filters if f.enabled]

    def get_enabled_processors(self) -> List[ProcessorConfig]:
        """Get list of enabled processors sorted by priority."""
        enabled = [p for p in self.processors if p.enabled]
        return sorted(enabled, key=lambda x: x.priority)


# ============================================================================
# Main Application Setup
# ============================================================================


def setup_logging() -> None:
    """Configure application logging."""
    loggerplusplus.add(
        sink=sys.stdout,
        level=InfraConfig.LOG_LEVEL,
        format=lpp_formats.ShortFormat(),
    )

    if InfraConfig.LOG_FILE:
        loggerplusplus.add(
            sink=InfraConfig.LOG_FILE,
            level=InfraConfig.LOG_LEVEL,
            format=lpp_formats.DetailedFormat(),
            rotation="100 MB",
            retention="30 days",
        )


def main() -> None:
    """Main application entry point."""

    print("=" * 80)
    print("FastAPI Document Search Application")
    print("=" * 80)

    # Setup logging
    setup_logging()
    logger = loggerplusplus.bind(identifier="STARTUP")

    # Display infrastructure configuration
    logger.info("Loading infrastructure configuration...")
    print(InfraConfig)

    # Validate infrastructure configuration
    try:
        InfraConfig.validate()
        logger.success("✅ Infrastructure configuration valid")
    except RuntimeError as e:
        logger.error(f"❌ Infrastructure configuration error: {e}")
        sys.exit(1)

    # Load application configuration
    logger.info("Loading application configuration...")
    try:
        app_config = AppConfig("config.yaml")
        print(app_config)
        logger.success("✅ Application configuration loaded")
    except Exception as e:
        logger.error(f"❌ Failed to load application configuration: {e}")
        sys.exit(1)

    # Display configuration summary
    print("\n" + "=" * 80)
    print("Configuration Summary")
    print("=" * 80)

    print(f"\n📌 Application")
    print(f"   Name: {InfraConfig.APP_NAME}")
    print(f"   Version: {InfraConfig.APP_VERSION}")
    print(f"   Environment: {InfraConfig.ENVIRONMENT}")

    print(f"\n🌐 Server")
    print(f"   Address: {InfraConfig.HOST}:{InfraConfig.PORT}")
    print(f"   Workers: {InfraConfig.WORKERS}")

    print(f"\n💾 Database")
    print(f"   PostgreSQL: {InfraConfig.DATABASE_HOST}:{InfraConfig.DATABASE_PORT}")
    print(f"   Redis: {InfraConfig.REDIS_HOST}:{InfraConfig.REDIS_PORT}")
    print(f"   Qdrant: {InfraConfig.QDRANT_URL}")

    print(f"\n🤖 AI Models")
    print(f"   Chat Model: {InfraConfig.OPENAI_MODEL}")
    print(f"   Embedding Model: {InfraConfig.OPENAI_EMBEDDING_MODEL}")

    print(f"\n🎨 UI Configuration")
    print(f"   Theme: {app_config.theme}")
    print(f"   Items per page: {app_config.items_per_page}")
    print(f"   Preview enabled: {app_config.enable_preview}")

    print(f"\n🔍 Search Configuration")
    print(f"   Max results: {app_config.max_results}")
    print(f"   Fuzzy matching: {app_config.fuzzy_matching}")

    print(f"\n📋 Filters ({len(app_config.get_enabled_filters())} enabled)")
    for filter_config in app_config.get_enabled_filters():
        print(f"   ✓ {filter_config.label} ({filter_config.type})")

    print(f"\n⚙️  Processors ({len(app_config.get_enabled_processors())} enabled)")
    for proc in app_config.get_enabled_processors():
        exts = ", ".join(proc.extensions)
        print(f"   ✓ {proc.name} [{exts}] (priority: {proc.priority})")

    print(f"\n🎯 Features")
    print(f"   CORS: {'✓' if InfraConfig.ENABLE_CORS else '✗'}")
    print(f"   API Docs: {'✓' if InfraConfig.ENABLE_DOCS else '✗'}")
    print(f"   Metrics: {'✓' if InfraConfig.ENABLE_METRICS else '✗'}")

    # Connection URLs (masked in logs)
    logger.debug(f"Database URL: {InfraConfig.get_database_url()}")
    logger.debug(f"Redis URL: {InfraConfig.get_redis_url()}")

    print("\n" + "=" * 80)
    logger.success("🚀 Application ready to start!")
    print("=" * 80)


if __name__ == "__main__":
    main()
