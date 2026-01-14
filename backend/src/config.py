"""
Configuration management for the stock selection system.
"""
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class TechnicalAnalysisConfig(BaseModel):
    """Configuration for technical analysis parameters."""

    # Moving Averages
    sma_periods: list[int] = Field(default=[20, 50, 200], description="Simple Moving Average periods")
    ema_periods: list[int] = Field(default=[12, 26, 50], description="Exponential Moving Average periods")

    # RSI Configuration
    rsi_period: int = Field(default=14, description="RSI calculation period")
    rsi_overbought: float = Field(default=70.0, description="RSI overbought threshold")
    rsi_oversold: float = Field(default=30.0, description="RSI oversold threshold")

    # MACD Configuration
    macd_fast: int = Field(default=12, description="MACD fast period")
    macd_slow: int = Field(default=26, description="MACD slow period")
    macd_signal: int = Field(default=9, description="MACD signal period")

    # Bollinger Bands
    bb_period: int = Field(default=20, description="Bollinger Bands period")
    bb_std: float = Field(default=2.0, description="Bollinger Bands standard deviation")

    # ATR Configuration
    atr_period: int = Field(default=14, description="ATR calculation period")

    # Volume Analysis
    volume_ma_period: int = Field(default=20, description="Volume moving average period")
    volume_spike_threshold: float = Field(default=2.0, description="Volume spike multiplier threshold")

    # Historical Data
    min_historical_days: int = Field(default=200, description="Minimum days of historical data required")

    # Scoring Weights (must sum to 100)
    weight_trend: float = Field(default=25.0, description="Weight for trend indicators")
    weight_momentum: float = Field(default=25.0, description="Weight for momentum indicators")
    weight_volatility: float = Field(default=20.0, description="Weight for volatility indicators")
    weight_volume: float = Field(default=30.0, description="Weight for volume analysis")


class DataSourceConfig(BaseModel):
    """Configuration for data sources and API keys."""

    alpha_vantage_api_key: str = Field(default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY", ""))
    polygon_api_key: str = Field(default_factory=lambda: os.getenv("POLYGON_API_KEY", ""))
    finnhub_api_key: str = Field(default_factory=lambda: os.getenv("FINNHUB_API_KEY", ""))

    # Rate limiting
    api_call_delay: float = Field(default=0.2, description="Delay between API calls in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")

    # Cache settings
    enable_cache: bool = Field(default=True, description="Enable data caching")
    cache_expiry_hours: int = Field(default=24, description="Cache expiry time in hours")


class AppConfig(BaseModel):
    """Main application configuration."""

    technical_analysis: TechnicalAnalysisConfig = Field(default_factory=TechnicalAnalysisConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)

    # General settings
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = Field(default_factory=lambda: os.getenv("LOG_FILE", "logs/trading.log"))

    # Stock filtering
    min_price: float = Field(default=5.0, description="Minimum stock price filter")
    min_volume: int = Field(default=500_000, description="Minimum daily volume filter")
    min_market_cap: float = Field(default=1_000_000_000, description="Minimum market cap (1B)")


# Singleton instance
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the application configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration (useful for testing)."""
    global _config
    _config = AppConfig()
    return _config

