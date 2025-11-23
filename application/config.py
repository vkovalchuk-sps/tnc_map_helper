"""Configuration management module"""

import json
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Manages application configuration"""

    def __init__(self, config_dir: Path) -> None:
        """
        Initialize ConfigManager

        Args:
            config_dir: Path to configuration directory
        """
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "settings.json"

    def get_config(self) -> Dict:
        """
        Get configuration from file

        Returns:
            Dictionary with configuration data
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, config: Dict) -> None:
        """
        Save configuration to file

        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # If save fails, continue working

    def get_language(self) -> str:
        """
        Get saved language from configuration

        Returns:
            Language code (UA or EN)
        """
        config = self.get_config()
        language = config.get("language", "EN")
        return language if language in ["UA", "EN"] else "EN"

    def save_language(self, language: str) -> None:
        """
        Save language to configuration

        Args:
            language: Language code (UA or EN)
        """
        config = self.get_config()
        config["language"] = language
        self.save_config(config)

    def get_last_author(self) -> Optional[str]:
        """
        Get last saved author from configuration

        Returns:
            Author name or None
        """
        config = self.get_config()
        return config.get("last_author")

    def save_last_author(self, author: str) -> None:
        """
        Save last author to configuration

        Args:
            author: Author name to save
        """
        if author:
            config = self.get_config()
            config["last_author"] = author
            self.save_config(config)

