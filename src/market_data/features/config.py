"""Feature configuration models and loader."""

from pathlib import Path
from typing import Optional, Union
import yaml

from pydantic import BaseModel, Field, ConfigDict


class IndicatorConfig(BaseModel):
    """Configuration for a single indicator."""
    
    model_config = ConfigDict(extra="forbid")
    
    name: str = Field(..., description="Indicator name (e.g., 'rsi', 'macd')")
    params: dict = Field(default_factory=dict, description="Indicator parameters")


class AssetClassConfig(BaseModel):
    """Configuration for a specific asset class."""
    
    model_config = ConfigDict(extra="forbid")
    
    asset_class: str = Field(..., description="Asset class name (e.g., 'equity', 'crypto')")
    indicators: list[IndicatorConfig] = Field(default_factory=list)


class FeatureConfig(BaseModel):
    """Root feature configuration."""
    
    model_config = ConfigDict(extra="forbid")
    
    version: str = Field(default="1.0", description="Config version")
    default: list[IndicatorConfig] = Field(
        default_factory=list,
        description="Default indicators applied to all assets",
    )
    asset_classes: list[AssetClassConfig] = Field(
        default_factory=list,
        description="Asset-class specific indicator overrides",
    )
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "FeatureConfig":
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file.
            
        Returns:
            Loaded FeatureConfig.
        """
        path = Path(path)
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
    
    @classmethod
    def from_dict(cls, data: dict) -> "FeatureConfig":
        """Load configuration from dictionary.
        
        Args:
            data: Configuration dictionary.
            
        Returns:
            Loaded FeatureConfig.
        """
        return cls.model_validate(data)
    
    def get_indicators(self, asset_class: Optional[str] = None) -> list[IndicatorConfig]:
        """Get indicators for a specific asset class.
        
        Args:
            asset_class: Asset class name, or None for defaults.
            
        Returns:
            List of indicator configurations.
        """
        if asset_class is None:
            return self.default
        
        # Look for asset-class specific config
        for ac_config in self.asset_classes:
            if ac_config.asset_class.lower() == asset_class.lower():
                return ac_config.indicators
        
        # Fall back to defaults
        return self.default
    
    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to YAML file.
        
        Args:
            path: Path to save YAML file.
        """
        path = Path(path)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
    
    @classmethod
    def default_config(cls) -> "FeatureConfig":
        """Create a default configuration with common indicators.
        
        Returns:
            Default FeatureConfig.
        """
        return cls(
            version="1.0",
            default=[
                IndicatorConfig(name="rsi", params={"length": 14}),
                IndicatorConfig(name="macd", params={"fast": 12, "slow": 26, "signal": 9}),
                IndicatorConfig(name="bbands", params={"length": 20, "std": 2.0}),
                IndicatorConfig(name="sma", params={"length": 20}),
                IndicatorConfig(name="sma", params={"length": 50}),
                IndicatorConfig(name="ema", params={"length": 12}),
                IndicatorConfig(name="ema", params={"length": 26}),
                IndicatorConfig(name="atr", params={"length": 14}),
                IndicatorConfig(name="volume_sma", params={"length": 20}),
            ],
            asset_classes=[
                AssetClassConfig(
                    asset_class="crypto",
                    indicators=[
                        IndicatorConfig(name="rsi", params={"length": 7}),
                        IndicatorConfig(name="macd", params={"fast": 8, "slow": 21, "signal": 5}),
                        IndicatorConfig(name="bbands", params={"length": 14, "std": 2.5}),
                        IndicatorConfig(name="ema", params={"length": 9}),
                        IndicatorConfig(name="ema", params={"length": 21}),
                        IndicatorConfig(name="atr", params={"length": 10}),
                    ],
                ),
            ],
        )
