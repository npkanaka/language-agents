import os
import yaml
import logging
from typing import Any, Dict

# Configure logging
logger = logging.getLogger(__name__)

class Config:
    """Singleton-based Configuration Manager for loading and accessing application settings."""
    
    _instance = None  # Singleton instance
    _config_data: Dict[str, Any] = {}  # Holds the loaded config data

    PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.yaml")

    def __new__(cls):
        """Ensures only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Loads config.yaml into memory and processes required transformations."""
        if not os.path.exists(self.CONFIG_PATH):
            logger.error(f"❌ Config file not found: {self.CONFIG_PATH}")
            raise FileNotFoundError(f"❌ Config file not found: {self.CONFIG_PATH}")

        with open(self.CONFIG_PATH, "r", encoding="utf-8") as file:
            self._config_data = yaml.safe_load(file) or {}

        self._resolve_paths()
        logger.info(f"✅ Config loaded successfully from {self.CONFIG_PATH}")

    def _resolve_paths(self) -> None:
        """Ensures all configured paths are resolved to absolute paths."""
        if "paths" in self._config_data:
            for key, relative_path in self._config_data["paths"].items():
                absolute_path = os.path.abspath(os.path.join(self.PROJECT_ROOT, relative_path))
                self._config_data["paths"][key] = absolute_path
                logger.debug(f"🔗 Resolved {key}: {absolute_path}")

    @classmethod
    def get(cls, key_path: str) -> Any:
        """Retrieves a nested configuration value."""
        instance = cls()
        keys = key_path.split(".")
        value = instance._config_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                logger.error(f"❌ Config key not found: {key_path}")
                raise KeyError(f"❌ Config key not found: {key_path}")

        return value

Config()  # Ensure Singleton is initialized
