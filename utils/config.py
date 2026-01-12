"""
Configuration management utilities
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger


class Config:
    """Configuration container."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        return self.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._config.copy()


def load_env(env_file: str = ".env") -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file
    """
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_file}")
    else:
        logger.warning(f"Environment file {env_file} not found")


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found, using defaults")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config or {}
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}


def load_config(
    config_file: Optional[str] = None,
    env_file: Optional[str] = None
) -> Config:
    """
    Load complete configuration from environment and config files.
    
    Args:
        config_file: Path to YAML config file
        env_file: Path to .env file
        
    Returns:
        Config object
    """
    # Load environment variables
    if env_file:
        load_env(env_file)
    else:
        load_env()
    
    # Load YAML config
    yaml_config = {}
    if config_file:
        yaml_config = load_yaml_config(config_file)
    
    # Merge with environment variables
    config_dict = {
        **yaml_config,
        "env": {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "gemini_api_key": os.getenv("GEMINI_API_KEY"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "yolo_model_path": os.getenv("YOLO_MODEL_PATH", "yolov8n.pt"),
            "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
            "reports_dir": os.getenv("REPORTS_DIR", "reports"),
            "uploads_dir": os.getenv("UPLOADS_DIR", "uploads")
        }
    }
    
    return Config(config_dict)


def get_detector_config() -> Dict[str, Any]:
    """Get detector configuration from environment."""
    return {
        "model_path": os.getenv("YOLO_MODEL_PATH", "yolov8n.pt"),
        "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
        "iou_threshold": float(os.getenv("IOU_THRESHOLD", "0.45")),
        "device": os.getenv("DEVICE", None),
        "verbose": os.getenv("VERBOSE", "false").lower() == "true"
    }


def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration from environment."""
    return {
        "provider": os.getenv("LLM_PROVIDER", "openai").lower(),
        "model": os.getenv("LLM_MODEL"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        "api_key": os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
    }


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup structured logging with loguru.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    from loguru import logger
    import sys
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # Add file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        "logs/siteguard_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    
    logger.info(f"Logging configured with level: {log_level}")


# Initialize on import
setup_logging(os.getenv("LOG_LEVEL", "INFO"))
