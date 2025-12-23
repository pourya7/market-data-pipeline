"""Yahoo Finance client implementation using yfinance."""

import asyncio
from datetime import date, datetime
from typing import Any

import yfinance as yf

from market_data.clients.base import BaseExchangeClient
from market_data.core.rate_limiter import RateLimiter
from market_data.core.retry import api_retry, TemporaryAPIError
from market_data.models.ohlcv import OHLCVBar


class YahooFinanceClient(BaseExchangeClient):
    """Yahoo Finance data client.
    
    Uses the yfinance library to fetch historical OHLCV data.
    Supports equities, ETFs, and some crypto pairs.
    
    Example:
        client = YahooFinanceClient()
        bars = await client.fetch_ohlcv("AAPL", "2024-01-01", "2024-01-31")
    """
    
    SUPPORTED_INTERVALS = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    
    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Yahoo Finance client.
        
        Args:
            config: Optional configuration with rate_limit setting.
        """
        super().__init__(config)
        rate_limit = self.config.get("rate_limit", 2000)  # requests per hour
        self._rate_limiter = RateLimiter.from_requests_per_hour(rate_limit)
    
    def get_provider_name(self) -> str:
        return "yahoo"
    
    def get_supported_intervals(self) -> list[str]:
        return self.SUPPORTED_INTERVALS.copy()
    
    @api_retry
    async def fetch_ohlcv(
        self,
        symbol: str,
        start_date: date | str,
        end_date: date | str,
        interval: str = "1d",
    ) -> list[OHLCVBar]:
        """Fetch OHLCV data from Yahoo Finance.
        
        Args:
            symbol: Ticker symbol (e.g., "AAPL", "MSFT").
            start_date: Start date for data retrieval.
            end_date: End date for data retrieval.
            interval: Bar interval (default "1d").
            
        Returns:
            List of OHLCVBar objects.
            
        Raises:
            ValueError: If symbol is invalid or interval not supported.
            TemporaryAPIError: If Yahoo Finance API fails.
        """
        # Validate inputs
        if not self.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol: {symbol}")
        
        if interval not in self.SUPPORTED_INTERVALS:
            raise ValueError(f"Unsupported interval: {interval}. Supported: {self.SUPPORTED_INTERVALS}")
        
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        
        if start > end:
            raise ValueError(f"start_date ({start}) must be <= end_date ({end})")
        
        # Rate limit
        await self._rate_limiter.acquire()
        
        # Fetch data in executor to avoid blocking
        try:
            bars = await asyncio.get_event_loop().run_in_executor(
                None,
                self._fetch_sync,
                symbol,
                start,
                end,
                interval,
            )
        except Exception as e:
            raise TemporaryAPIError(f"Yahoo Finance API error: {e}") from e
        
        return bars
    
    def _fetch_sync(
        self,
        symbol: str,
        start: date,
        end: date,
        interval: str,
    ) -> list[OHLCVBar]:
        """Synchronous data fetch using yfinance."""
        ticker = yf.Ticker(symbol)
        
        # yfinance uses string dates
        df = ticker.history(
            start=start.isoformat(),
            end=end.isoformat(),
            interval=interval,
            auto_adjust=False,  # Keep raw OHLCV, we'll handle adjustments
        )
        
        if df.empty:
            return []
        
        bars = []
        for timestamp, row in df.iterrows():
            # Skip rows with NaN values
            if row.isna().any():
                continue
            
            # Handle timezone-aware timestamps
            if hasattr(timestamp, "tzinfo") and timestamp.tzinfo is not None:
                ts = timestamp.to_pydatetime()
            else:
                ts = datetime.combine(timestamp.date(), datetime.min.time())
            
            bar = OHLCVBar(
                timestamp=ts,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                symbol=symbol.upper(),
                provider=self.get_provider_name(),
                interval=interval,
            )
            bars.append(bar)
        
        return bars
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate Yahoo Finance ticker symbol.
        
        Basic validation - actual ticker existence checked during fetch.
        """
        if not symbol or not symbol.strip():
            return False
        # Allow alphanumeric, dots, dashes, carets (for indices)
        clean = symbol.strip().upper()
        return all(c.isalnum() or c in ".-^=" for c in clean)
