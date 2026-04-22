from __future__ import annotations

from pathlib import Path


class ConfigError(Exception):
    """Base error for configuration loading."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the configuration file does not exist."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"Config file does not exist: {path}")
        self.path = path
