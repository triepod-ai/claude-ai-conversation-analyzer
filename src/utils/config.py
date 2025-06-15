"""
Configuration management for Claude AI Conversation Analyzer Portfolio.
Handles environment variables and application settings.
"""

import os
from typing import Optional, Union
from pathlib import Path


class Config:
    """Application configuration management."""
    
    def __init__(self):
        self._load_env_file()
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Only set if not already in environment
                        if key not in os.environ:
                            os.environ[key] = value
    
    def get(self, key: str, default: Optional[Union[str, int, bool]] = None) -> str:
        """Get configuration value with optional default."""
        return os.getenv(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        try:
            return int(self.get(key, str(default)))
        except (ValueError, TypeError):
            return default
    
    # Application Settings
    @property
    def flask_env(self) -> str:
        return self.get('FLASK_ENV', 'production')
    
    @property
    def flask_app(self) -> str:
        return self.get('FLASK_APP', 'demo/app.py')
    
    @property
    def secret_key(self) -> str:
        return self.get('FLASK_SECRET_KEY', 'portfolio-demo-key-change-in-production')
    
    @property
    def host(self) -> str:
        return self.get('HOST', '0.0.0.0')
    
    @property
    def port(self) -> int:
        return self.get_int('PORT', 5000)
    
    @property
    def debug(self) -> bool:
        return self.get_bool('FLASK_DEBUG', False)
    
    # Database Configuration
    @property
    def chroma_host(self) -> str:
        return self.get('CHROMA_HOST', 'localhost')
    
    @property
    def chroma_port(self) -> int:
        return self.get_int('CHROMA_PORT', 8001)
    
    @property
    def chroma_collection_name(self) -> str:
        return self.get('CHROMA_COLLECTION_NAME', 'claude_project_chats')
    
    @property
    def chroma_persist_directory(self) -> str:
        return self.get('CHROMA_PERSIST_DIRECTORY', './data/chroma_db')
    
    # Demo Configuration
    @property
    def demo_mode(self) -> bool:
        return self.get_bool('DEMO_MODE', True)
    
    @property
    def mock_data_path(self) -> str:
        return self.get('MOCK_DATA_PATH', './data/mock_conversations.json')
    
    @property
    def chunks_data_path(self) -> str:
        return self.get('CHUNKS_DATA_PATH', './data/conversation_chunks.json')
    
    @property
    def enable_real_time_stats(self) -> bool:
        return self.get_bool('ENABLE_REAL_TIME_STATS', True)
    
    # Performance Settings
    @property
    def max_search_results(self) -> int:
        return self.get_int('MAX_SEARCH_RESULTS', 50)
    
    @property
    def search_timeout_seconds(self) -> int:
        return self.get_int('SEARCH_TIMEOUT_SECONDS', 30)
    
    @property
    def chunk_size(self) -> int:
        return self.get_int('CHUNK_SIZE', 1200)
    
    @property
    def chunk_overlap(self) -> int:
        return self.get_int('CHUNK_OVERLAP', 200)
    
    # Security Settings
    @property
    def enable_rate_limiting(self) -> bool:
        return self.get_bool('ENABLE_RATE_LIMITING', True)
    
    @property
    def api_rate_limit(self) -> int:
        return self.get_int('API_RATE_LIMIT', 100)
    
    @property
    def search_rate_limit(self) -> int:
        return self.get_int('SEARCH_RATE_LIMIT', 20)
    
    @property
    def cors_origins(self) -> str:
        return self.get('CORS_ORIGINS', '*')
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        return self.get('LOG_LEVEL', 'INFO')
    
    @property
    def log_file(self) -> str:
        return self.get('LOG_FILE', './logs/app.log')
    
    @property
    def enable_debug_logging(self) -> bool:
        return self.get_bool('ENABLE_DEBUG_LOGGING', False)
    
    # Analytics
    @property
    def enable_analytics(self) -> bool:
        return self.get_bool('ENABLE_ANALYTICS', False)
    
    @property
    def analytics_api_key(self) -> str:
        return self.get('ANALYTICS_API_KEY', '')
    
    @property
    def google_analytics_id(self) -> str:
        return self.get('GOOGLE_ANALYTICS_ID', '')
    
    # External Services
    @property
    def sentry_dsn(self) -> str:
        return self.get('SENTRY_DSN', '')
    
    @property
    def monitoring_webhook_url(self) -> str:
        return self.get('MONITORING_WEBHOOK_URL', '')
    
    # Development Settings
    @property
    def reload_on_change(self) -> bool:
        return self.get_bool('RELOAD_ON_CHANGE', False)
    
    @property
    def show_performance_metrics(self) -> bool:
        return self.get_bool('SHOW_PERFORMANCE_METRICS', True)


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    
    def __init__(self):
        super().__init__()
        # Override defaults for development
        os.environ.setdefault('FLASK_ENV', 'development')
        os.environ.setdefault('FLASK_DEBUG', 'true')
        os.environ.setdefault('LOG_LEVEL', 'DEBUG')
        os.environ.setdefault('ENABLE_DEBUG_LOGGING', 'true')


class ProductionConfig(Config):
    """Production-specific configuration."""
    
    def __init__(self):
        super().__init__()
        # Override defaults for production
        os.environ.setdefault('FLASK_ENV', 'production')
        os.environ.setdefault('FLASK_DEBUG', 'false')
        os.environ.setdefault('LOG_LEVEL', 'INFO')
        os.environ.setdefault('ENABLE_RATE_LIMITING', 'true')


class TestingConfig(Config):
    """Testing-specific configuration."""
    
    def __init__(self):
        super().__init__()
        # Override defaults for testing
        os.environ.setdefault('FLASK_ENV', 'testing')
        os.environ.setdefault('DEMO_MODE', 'true')
        os.environ.setdefault('CHROMA_PERSIST_DIRECTORY', './test_data/chroma_db')


def get_config_by_name(config_name: str) -> Config:
    """Get configuration by name."""
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': Config
    }
    
    config_class = configs.get(config_name, Config)
    return config_class()