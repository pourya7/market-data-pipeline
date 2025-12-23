"""Tests for client factory."""

import pytest

from market_data.factory import ClientFactory
from market_data.clients.base import BaseExchangeClient
from market_data.clients.yahoo import YahooFinanceClient
from market_data.clients.polygon import PolygonClient
from market_data.clients.oanda import OandaClient
from market_data.core.config import PipelineConfig, ProviderConfig


class TestClientFactory:
    """Tests for ClientFactory class."""
    
    def test_create_yahoo_client(self):
        """Test creating Yahoo Finance client."""
        client = ClientFactory.create("yahoo")
        
        assert isinstance(client, YahooFinanceClient)
        assert client.get_provider_name() == "yahoo"
    
    def test_create_polygon_client(self):
        """Test creating Polygon client."""
        client = ClientFactory.create("polygon", {"api_key": "test_key"})
        
        assert isinstance(client, PolygonClient)
        assert client.get_provider_name() == "polygon"
    
    def test_create_oanda_client(self):
        """Test creating Oanda client."""
        client = ClientFactory.create("oanda", {
            "api_key": "test_key",
            "account_id": "test_account"
        })
        
        assert isinstance(client, OandaClient)
        assert client.get_provider_name() == "oanda"
    
    def test_create_case_insensitive(self):
        """Test that provider names are case-insensitive."""
        client1 = ClientFactory.create("Yahoo")
        client2 = ClientFactory.create("YAHOO")
        client3 = ClientFactory.create("yahoo")
        
        assert all(isinstance(c, YahooFinanceClient) for c in [client1, client2, client3])
    
    def test_create_unknown_provider_raises(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ClientFactory.create("unknown_provider")
        
        assert "unknown_provider" in str(exc_info.value).lower()
        assert "available" in str(exc_info.value).lower()
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = ClientFactory.get_available_providers()
        
        assert "yahoo" in providers
        assert "polygon" in providers
        assert "oanda" in providers
    
    def test_is_registered(self):
        """Test checking if provider is registered."""
        assert ClientFactory.is_registered("yahoo")
        assert ClientFactory.is_registered("YAHOO")
        assert not ClientFactory.is_registered("unknown")
    
    def test_from_config(self):
        """Test creating client from pipeline config."""
        config = PipelineConfig(
            providers={
                "yahoo": ProviderConfig(enabled=True, rate_limit=1000),
            }
        )
        
        client = ClientFactory.from_config("yahoo", config)
        
        assert isinstance(client, YahooFinanceClient)
    
    def test_from_config_disabled_provider_raises(self):
        """Test that disabled provider raises ValueError."""
        config = PipelineConfig(
            providers={
                "yahoo": ProviderConfig(enabled=False),
            }
        )
        
        with pytest.raises(ValueError) as exc_info:
            ClientFactory.from_config("yahoo", config)
        
        assert "not found or not enabled" in str(exc_info.value)
    
    def test_from_config_missing_provider_raises(self):
        """Test that missing provider raises ValueError."""
        config = PipelineConfig()
        
        with pytest.raises(ValueError):
            ClientFactory.from_config("polygon", config)
    
    def test_register_custom_client(self):
        """Test registering a custom client."""
        class CustomClient(BaseExchangeClient):
            async def fetch_ohlcv(self, symbol, start, end, interval="1d"):
                return []
            
            def get_provider_name(self):
                return "custom"
            
            def get_supported_intervals(self):
                return ["1d"]
        
        ClientFactory.register("custom", CustomClient)
        
        assert ClientFactory.is_registered("custom")
        client = ClientFactory.create("custom")
        assert isinstance(client, CustomClient)
        
        # Cleanup
        del ClientFactory._registry["custom"]
    
    def test_register_invalid_class_raises(self):
        """Test that registering non-BaseExchangeClient raises."""
        class NotAClient:
            pass
        
        with pytest.raises(TypeError):
            ClientFactory.register("invalid", NotAClient)
