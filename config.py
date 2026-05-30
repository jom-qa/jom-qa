"""Configuration management for jom-qa engine."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Main application configuration."""
    
    # Parser settings
    parser_extract_tables: bool = False
    parser_encoding: str = 'utf-8'
    
    # API settings
    api_host: str = '0.0.0.0'
    api_port: int = 8000
    api_debug: bool = False
    
    # Logging settings
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    
    # Output settings
    output_dir: str = 'output'
    
    # AI Integration settings
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = 'anthropic/claude-3-haiku'
    
    # MCP settings
    mcp_enabled: bool = True
    mcp_port: int = 3000
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load configuration from environment variables."""
        return cls(
            parser_extract_tables=os.getenv('PARSER_EXTRACT_TABLES', 'false').lower() == 'true',
            parser_encoding=os.getenv('PARSER_ENCODING', 'utf-8'),
            api_host=os.getenv('API_HOST', '0.0.0.0'),
            api_port=int(os.getenv('API_PORT', '8000')),
            api_debug=os.getenv('API_DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE'),
            output_dir=os.getenv('OUTPUT_DIR', 'output'),
            openrouter_api_key=os.getenv('OPENROUTER_API_KEY'),
            openrouter_model=os.getenv('OPENROUTER_MODEL', 'anthropic/claude-3-haiku'),
            mcp_enabled=os.getenv('MCP_ENABLED', 'true').lower() == 'true',
            mcp_port=int(os.getenv('MCP_PORT', '3000'))
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'AppConfig':
        """Load configuration from JSON file."""
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(**data)
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
    
    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        log_config = {
            'level': getattr(logging, self.log_level.upper()),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
        
        if self.log_file:
            log_config['filename'] = self.log_file
        
        logging.basicConfig(**log_config)
        logger.setLevel(log_config['level'])
        logger.info(f"Logging configured at {self.log_level} level")


def get_config(config_path: Optional[str] = None) -> AppConfig:
    """
    Get application configuration.
    
    Args:
        config_path: Optional path to config file. If not provided, checks for
                    config.json in current directory, then uses env vars.
    
    Returns:
        AppConfig instance
    """
    # Try config file first
    if config_path:
        return AppConfig.from_file(config_path)
    
    # Check for default config.json
    default_config = Path('config.json')
    if default_config.exists():
        logger.info(f"Loading configuration from {default_config}")
        return AppConfig.from_file(str(default_config))
    
    # Fall back to environment variables
    logger.info("Loading configuration from environment variables")
    return AppConfig.from_env()
