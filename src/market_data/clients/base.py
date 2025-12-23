"""Abstract base class for exchange clients."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from market_data.models.ohlcv import OHLCVBar


class BaseExchangeClient(ABC):
    """Abstract base class for all exchange/data provider clients.
    
    Provides a unified interface for fetching OHLCV data from different
    data sources. All provider-specific clients must inherit from this
    class and implement the abstract methods.
    
    Example:
        class MyProviderClient(BaseExchangeClient):
            async def fetch_ohlcv(self, symbol, start_date, end_date, interval):
                # Provider-specific implementation
                ...
    """
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the client with optional configuration.
        
        Args:
            config: Provider-specific configuration dictionary.
        """
        self.config = config or {}
    
    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        start_date: date | str,
        end_date: date | str,
        interval: str = "1d",
    ) -> list[OHLCVBar]:
        """Fetch OHLCV data for a symbol within a date range.
        
        Args:
            symbol: Ticker symbol (e.g., "AAPL", "EUR/USD").
            start_date: Start date for data retrieval.
            end_date: End date for data retrieval.
            interval: Bar interval (e.g., "1m", "5m", "1h", "1d").
            
        Returns:
            List of OHLCVBar objects sorted by timestamp ascending.
            
        Raises:
            ValueError: If symbol is invalid or date range is incorrect.
            ConnectionError: If API connection fails.
        """
        ...
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the data provider.
        
        Returns:
            Provider name string (e.g., "yahoo", "polygon", "oanda").
        """
        ...
    
    @abstractmethod
    def get_supported_intervals(self) -> list[str]:
        """Return list of supported bar intervals.
        
        Returns:
            List of interval strings (e.g., ["1m", "5m", "1h", "1d"]).
        """
        ...
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is supported by this provider.
        
        Default implementation accepts any non-empty string.
        Override in subclasses for provider-specific validation.
        
        Args:
            symbol: Ticker symbol to validate.
            
        Returns:
            True if symbol is valid, False otherwise.
        """
        return bool(symbol and symbol.strip())
    
    def _parse_date(self, d: date | str) -> date:
        """Parse date from string or date object.
        
        Args:
            d: Date as string (YYYY-MM-DD) or date object.
            
        Returns:
            Parsed date object.
        """
        if isinstance(d, str):
            return date.fromisoformat(d)
        return d
