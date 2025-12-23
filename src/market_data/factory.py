"""Client factory for creating exchange clients."""

from typing import Any

from market_data.clients.base import BaseExchangeClient
from market_data.clients.yahoo import YahooFinanceClient
from market_data.clients.polygon import PolygonClient
from market_data.clients.oanda import OandaClient
from market_data.core.config import PipelineConfig, ProviderConfig


class ClientFactory:
    """Factory for creating exchange client instances.
    
    Provides a unified interface for instantiating provider-specific
    clients based on configuration.
    
    Example:
        # Simple usage
        client = ClientFactory.create("yahoo")
        
        # With configuration
        config = load_config("config.yaml")
        client = ClientFactory.from_config("polygon", config)
    """
    
    _registry: dict[str, type[BaseExchangeClient]] = {
        "yahoo": YahooFinanceClient,
        "polygon": PolygonClient,
        "oanda": OandaClient,
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        config: dict[str, Any] | None = None,
    ) -> BaseExchangeClient:
        """Create a client instance for the specified provider.
        
        Args:
            provider: Provider name (e.g., "yahoo", "polygon", "oanda").
            config: Optional provider-specific configuration.
            
        Returns:
            Configured client instance.
            
        Raises:
            ValueError: If provider is not registered.
        """
        provider_lower = provider.lower()
        
        if provider_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown provider: {provider}. Available: {available}")
        
        client_class = cls._registry[provider_lower]
        return client_class(config)
    
    @classmethod
    def from_config(
        cls,
        provider: str,
        pipeline_config: PipelineConfig,
    ) -> BaseExchangeClient:
        """Create a client using pipeline configuration.
        
        Args:
            provider: Provider name.
            pipeline_config: Full pipeline configuration.
            
        Returns:
            Configured client instance.
            
        Raises:
            ValueError: If provider not found or not enabled.
        """
        provider_config = pipeline_config.get_provider(provider)
        
        if provider_config is None:
            raise ValueError(f"Provider '{provider}' not found or not enabled in config")
        
        # Convert ProviderConfig to dict for client
        config_dict = {
            "api_key": provider_config.api_key,
            "rate_limit": provider_config.rate_limit,
            "timeout": provider_config.timeout,
            **provider_config.extra,
        }
        
        return cls.create(provider, config_dict)
    
    @classmethod
    def register(cls, name: str, client_class: type[BaseExchangeClient]) -> None:
        """Register a new client class.
        
        Allows adding custom providers at runtime.
        
        Args:
            name: Provider name.
            client_class: Client class (must inherit from BaseExchangeClient).
            
        Raises:
            TypeError: If client_class doesn't inherit from BaseExchangeClient.
        """
        if not issubclass(client_class, BaseExchangeClient):
            raise TypeError(f"{client_class} must inherit from BaseExchangeClient")
        
        cls._registry[name.lower()] = client_class
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Return list of registered provider names."""
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, provider: str) -> bool:
        """Check if a provider is registered."""
        return provider.lower() in cls._registry
