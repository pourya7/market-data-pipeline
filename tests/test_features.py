"""Tests for the Feature Engineering module."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from market_data.features.technical import TechnicalAnalyzer
from market_data.features.config import FeatureConfig, IndicatorConfig, AssetClassConfig
from market_data.features.pipeline import FeaturePipeline


@pytest.fixture
def sample_ohlcv_df():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    n = 100
    
    dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
    
    # Generate realistic price data
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    high = close + np.abs(np.random.randn(n) * 1.5)
    low = close - np.abs(np.random.randn(n) * 1.5)
    open_price = close + np.random.randn(n) * 0.5
    volume = np.random.randint(1000000, 10000000, n).astype(float)
    
    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)


class TestTechnicalAnalyzer:
    """Tests for TechnicalAnalyzer class."""
    
    def test_add_rsi(self, sample_ohlcv_df):
        """Test RSI calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_rsi(sample_ohlcv_df, length=14)
        
        assert "rsi_14" in result.columns
        assert len(result) == len(sample_ohlcv_df)
        
        # RSI should be between 0 and 100
        valid_rsi = result["rsi_14"].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_add_rsi_custom_length(self, sample_ohlcv_df):
        """Test RSI with custom length."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_rsi(sample_ohlcv_df, length=7)
        
        assert "rsi_7" in result.columns
    
    def test_add_macd(self, sample_ohlcv_df):
        """Test MACD calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_macd(sample_ohlcv_df)
        
        assert "macd_12_26_9" in result.columns
        assert "macd_signal_12_26_9" in result.columns
        assert "macd_hist_12_26_9" in result.columns
    
    def test_add_macd_custom_params(self, sample_ohlcv_df):
        """Test MACD with custom parameters."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_macd(sample_ohlcv_df, fast=8, slow=21, signal=5)
        
        assert "macd_8_21_5" in result.columns
    
    def test_add_bbands(self, sample_ohlcv_df):
        """Test Bollinger Bands calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_bbands(sample_ohlcv_df, length=20, std=2.0)
        
        assert "bband_lower_20" in result.columns
        assert "bband_mid_20" in result.columns
        assert "bband_upper_20" in result.columns
        assert "bband_bandwidth_20" in result.columns
        assert "bband_percent_20" in result.columns
        
        # Upper should be greater than lower
        valid_idx = result["bband_upper_20"].notna()
        assert (result.loc[valid_idx, "bband_upper_20"] >= 
                result.loc[valid_idx, "bband_lower_20"]).all()
    
    def test_add_sma(self, sample_ohlcv_df):
        """Test SMA calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_sma(sample_ohlcv_df, length=20)
        
        assert "sma_20" in result.columns
        
        # SMA should start producing values after length periods
        assert result["sma_20"].isna().sum() == 19  # 20-1 NaN values
    
    def test_add_ema(self, sample_ohlcv_df):
        """Test EMA calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_ema(sample_ohlcv_df, length=12)
        
        assert "ema_12" in result.columns
    
    def test_add_atr(self, sample_ohlcv_df):
        """Test ATR calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_atr(sample_ohlcv_df, length=14)
        
        assert "atr_14" in result.columns
        
        # ATR should be positive
        valid_atr = result["atr_14"].dropna()
        assert (valid_atr >= 0).all()
    
    def test_add_stochastic(self, sample_ohlcv_df):
        """Test Stochastic Oscillator calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_stochastic(sample_ohlcv_df)
        
        assert "stoch_k_14" in result.columns
        assert "stoch_d_14_3" in result.columns
        
        # Stochastic should be between 0 and 100
        valid_k = result["stoch_k_14"].dropna()
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
    
    def test_add_volume_sma(self, sample_ohlcv_df):
        """Test Volume SMA calculation."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_volume_sma(sample_ohlcv_df, length=20)
        
        assert "volume_sma_20" in result.columns
    
    def test_add_defaults(self, sample_ohlcv_df):
        """Test adding all default indicators."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.add_defaults(sample_ohlcv_df)
        
        # Check for key indicators
        assert "rsi_14" in result.columns
        assert "macd_12_26_9" in result.columns
        assert "bband_mid_20" in result.columns
        assert "sma_20" in result.columns
        assert "sma_50" in result.columns
        assert "ema_12" in result.columns
        assert "atr_14" in result.columns
    
    def test_apply_indicators(self, sample_ohlcv_df):
        """Test applying indicators from config list."""
        analyzer = TechnicalAnalyzer()
        
        indicators = [
            {"name": "rsi", "params": {"length": 14}},
            {"name": "sma", "params": {"length": 20}},
        ]
        
        result = analyzer.apply_indicators(sample_ohlcv_df, indicators)
        
        assert "rsi_14" in result.columns
        assert "sma_20" in result.columns
    
    def test_apply_indicators_unknown_raises(self, sample_ohlcv_df):
        """Test that unknown indicator raises error."""
        analyzer = TechnicalAnalyzer()
        
        indicators = [{"name": "unknown_indicator", "params": {}}]
        
        with pytest.raises(ValueError, match="Unknown indicator"):
            analyzer.apply_indicators(sample_ohlcv_df, indicators)
    
    def test_get_available_indicators(self):
        """Test getting list of available indicators."""
        analyzer = TechnicalAnalyzer()
        indicators = analyzer.get_available_indicators()
        
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "bbands" in indicators


class TestFeatureConfig:
    """Tests for FeatureConfig class."""
    
    def test_default_config(self):
        """Test creating default configuration."""
        config = FeatureConfig.default_config()
        
        assert config.version == "1.0"
        assert len(config.default) > 0
        assert len(config.asset_classes) > 0
    
    def test_from_dict(self):
        """Test loading config from dictionary."""
        data = {
            "version": "1.0",
            "default": [
                {"name": "rsi", "params": {"length": 14}},
            ],
        }
        
        config = FeatureConfig.from_dict(data)
        
        assert config.version == "1.0"
        assert len(config.default) == 1
        assert config.default[0].name == "rsi"
    
    def test_get_indicators_default(self):
        """Test getting default indicators."""
        config = FeatureConfig.default_config()
        indicators = config.get_indicators()
        
        assert len(indicators) > 0
        assert all(isinstance(i, IndicatorConfig) for i in indicators)
    
    def test_get_indicators_asset_class(self):
        """Test getting asset-class specific indicators."""
        config = FeatureConfig.default_config()
        crypto_indicators = config.get_indicators("crypto")
        
        # Should have crypto-specific config
        assert len(crypto_indicators) > 0
        
        # RSI length for crypto should be 7, not 14
        rsi_config = next((i for i in crypto_indicators if i.name == "rsi"), None)
        assert rsi_config is not None
        assert rsi_config.params.get("length") == 7
    
    def test_get_indicators_unknown_asset_class(self):
        """Test that unknown asset class falls back to default."""
        config = FeatureConfig.default_config()
        indicators = config.get_indicators("unknown_asset")
        
        # Should fall back to defaults
        assert indicators == config.default


class TestFeaturePipeline:
    """Tests for FeaturePipeline class."""
    
    def test_calculate_features(self, sample_ohlcv_df):
        """Test calculating features."""
        pipeline = FeaturePipeline()
        result = pipeline.calculate_features(sample_ohlcv_df)
        
        assert len(pipeline.last_features) > 0
        assert all(f in result.columns for f in pipeline.last_features)
    
    def test_calculate_features_with_asset_class(self, sample_ohlcv_df):
        """Test calculating features for specific asset class."""
        pipeline = FeaturePipeline()
        result = pipeline.calculate_features(sample_ohlcv_df, asset_class="crypto")
        
        # Should have crypto-specific RSI (length 7)
        assert "rsi_7" in result.columns
    
    def test_calculate_features_with_custom_indicators(self, sample_ohlcv_df):
        """Test calculating features with custom indicator list."""
        pipeline = FeaturePipeline()
        
        custom_indicators = [
            IndicatorConfig(name="rsi", params={"length": 21}),
            IndicatorConfig(name="sma", params={"length": 100}),
        ]
        
        result = pipeline.calculate_features(
            sample_ohlcv_df,
            indicators=custom_indicators,
        )
        
        assert "rsi_21" in result.columns
        assert "sma_100" in result.columns
    
    def test_calculate_defaults(self, sample_ohlcv_df):
        """Test calculate_defaults convenience method."""
        pipeline = FeaturePipeline()
        result = pipeline.calculate_defaults(sample_ohlcv_df)
        
        assert "rsi_14" in result.columns
        assert "macd_12_26_9" in result.columns
    
    def test_get_feature_columns(self, sample_ohlcv_df):
        """Test getting feature column names."""
        pipeline = FeaturePipeline()
        
        df_with_features = pipeline.calculate_defaults(sample_ohlcv_df)
        feature_cols = pipeline.get_feature_columns(df_with_features)
        
        assert len(feature_cols) > 0
        assert "close" not in feature_cols
        assert "rsi_14" in feature_cols
    
    def test_has_features(self, sample_ohlcv_df):
        """Test checking if DataFrame has features."""
        pipeline = FeaturePipeline()
        
        assert not pipeline.has_features(sample_ohlcv_df)
        
        df_with_features = pipeline.calculate_defaults(sample_ohlcv_df)
        assert pipeline.has_features(df_with_features)
    
    def test_save_without_storage_raises(self, sample_ohlcv_df):
        """Test that save without storage manager raises error."""
        pipeline = FeaturePipeline()
        
        with pytest.raises(ValueError, match="Storage manager not configured"):
            pipeline.save_with_features(sample_ohlcv_df, "TEST")
    
    def test_load_without_storage_raises(self):
        """Test that load without storage manager raises error."""
        pipeline = FeaturePipeline()
        
        with pytest.raises(ValueError, match="Storage manager not configured"):
            pipeline.load_with_features("TEST")
