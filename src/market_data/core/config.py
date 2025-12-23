"""Configuration loader with Pydantic validation."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class ProviderConfig(BaseModel):
    """Configuration for a single data provider."""
    
    enabled: bool = True
    api_key: str | None = None
    rate_limit: float = Field(default=60.0, description="Requests per minute")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    extra: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env_var(cls, v: str | None) -> str | None:
        """Resolve environment variable references like ${VAR_NAME}."""
        if v is None:
            return None
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.environ.get(env_var)
        return v


class PipelineConfig(BaseModel):
    """Root configuration for the market data pipeline."""
    
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    storage_path: Path = Field(default=Path("./data"))
    log_level: str = Field(default="INFO")
    
    model_config = {
        "str_strip_whitespace": True,
    }
    
    def get_provider(self, name: str) -> ProviderConfig | None:
        """Get configuration for a specific provider.
        
        Args:
            name: Provider name (e.g., "yahoo", "polygon").
            
        Returns:
            ProviderConfig if found and enabled, None otherwise.
        """
        config = self.providers.get(name.lower())
        if config and config.enabled:
            return config
        return None
    
    def get_enabled_providers(self) -> list[str]:
        """Return list of enabled provider names."""
        return [
            name for name, config in self.providers.items()
            if config.enabled
        ]


def load_config(path: str | Path | None = None) -> PipelineConfig:
    """Load configuration from a YAML file.
    
    Args:
        path: Path to config file. If None, returns default config.
        
    Returns:
        Validated PipelineConfig instance.
        
    Raises:
        FileNotFoundError: If path is specified but file doesn't exist.
        ValueError: If config file is invalid.
    """
    if path is None:
        return PipelineConfig()
    
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path) as f:
        raw_config = yaml.safe_load(f)
    
    if raw_config is None:
        return PipelineConfig()
    
    return PipelineConfig.model_validate(raw_config)


def create_default_config() -> dict[str, Any]:
    """Create a default configuration dictionary.
    
    Useful for generating example config files.
    
    Returns:
        Dictionary with default configuration values.
    """
    return {
        "providers": {
            "yahoo": {
                "enabled": True,
                "rate_limit": 2000,  # Yahoo is quite permissive
            },
            "polygon": {
                "enabled": False,
                "api_key": "${POLYGON_API_KEY}",
                "rate_limit": 5,  # Free tier limit
            },
            "oanda": {
                "enabled": False,
                "api_key": "${OANDA_API_KEY}",
                "rate_limit": 30,
            },
        },
        "storage_path": "./data",
        "log_level": "INFO",
    }
