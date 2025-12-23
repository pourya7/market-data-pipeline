"""Integration test fixtures."""

import pytest


@pytest.fixture
def mock_yahoo_response():
    """Mock Yahoo Finance API response data."""
    return {
        "chart": {
            "result": [{
                "meta": {
                    "symbol": "AAPL",
                    "currency": "USD",
                    "regularMarketPrice": 185.0,
                },
                "timestamp": [1704153600, 1704240000, 1704326400],
                "indicators": {
                    "quote": [{
                        "open": [182.5, 183.0, 184.5],
                        "high": [185.0, 186.0, 187.0],
                        "low": [181.0, 182.0, 183.0],
                        "close": [184.0, 185.0, 186.0],
                        "volume": [100000, 110000, 120000],
                    }],
                    "adjclose": [{
                        "adjclose": [184.0, 185.0, 186.0],
                    }],
                },
            }],
            "error": None,
        }
    }


@pytest.fixture
def mock_empty_response():
    """Mock empty API response."""
    return {
        "chart": {
            "result": None,
            "error": {
                "code": "Not Found",
                "description": "No data found",
            }
        }
    }
