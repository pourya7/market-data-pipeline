"""Polygon.io client implementation (stub)."""

from datetime import date
from typing import Any

from market_data.clients.base import BaseExchangeClient
from market_data.core.rate_limiter import RateLimiter
from market_data.models.ohlcv import OHLCVBar


class PolygonClient(BaseExchangeClient):
    """Polygon.io data client.
    
    Provides access to US equities, options, forex, and crypto data.
    Requires API key from polygon.io.
    
    Note: This is a stub implementation. Full implementation requires
    API key and additional endpoint configuration.
    
    Example:
        client = PolygonClient(config={"api_key": "your_key"})
        bars = await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-31")
    """
    
    SUPPORTED_INTERVALS = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Polygon client.
        
        Args:
            config: Configuration with api_key and rate_limit.
        """
        super().__init__(config)
        self._api_key = self.config.get("api_key")
        rate_limit = self.config.get("rate_limit", 5)  # Free tier: 5 req/min
        self._rate_limiter = RateLimiter.from_requests_per_minute(rate_limit)
    
    def get_provider_name(self) -> str:
        return "polygon"
    
    def get_supported_intervals(self) -> list[str]:
        return self.SUPPORTED_INTERVALS.copy()
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        start_date: date | str,
        end_date: date | str,
        interval: str = "1d",
    ) -> list[OHLCVBar]:
        """Fetch OHLCV data from Polygon.io.
        
        Args:
            symbol: Ticker symbol.
            start_date: Start date.
            end_date: End date.
            interval: Bar interval.
            
        Returns:
            List of OHLCVBar objects.
            
        Raises:
            NotImplementedError: This is a stub implementation.
        """
        if not self._api_key:
            raise ValueError("Polygon API key required. Set 'api_key' in config.")
        
        # Validate inputs
        if not self.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        if interval not in self.SUPPORTED_INTERVALS:
            raise ValueError(f"Unsupported interval: {interval}")
        
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        
        if start > end:
            raise ValueError(f"start_date ({start}) must be <= end_date ({end})")
        
        # Rate limit
        await self._rate_limiter.acquire()
        
        # TODO: Implement actual API call
        # Endpoint: GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        # Headers: Authorization: Bearer {api_key}
        
        raise NotImplementedError(
            "Polygon client fetch_ohlcv not yet implemented. "
            "See https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to"
        )
    
    def _interval_to_polygon(self, interval: str) -> tuple[int, str]:
        """Convert interval string to Polygon multiplier/timespan.
        
        Args:
            interval: Interval string like "1d", "5m".
            
        Returns:
            Tuple of (multiplier, timespan).
        """
        mapping = {
            "1m": (1, "minute"),
            "5m": (5, "minute"),
            "15m": (15, "minute"),
            "30m": (30, "minute"),
            "1h": (1, "hour"),
            "1d": (1, "day"),
            "1wk": (1, "week"),
            "1mo": (1, "month"),
        }
        return mapping.get(interval, (1, "day"))
