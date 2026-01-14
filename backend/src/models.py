"""
Data models for stock analysis.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ConfidenceLevel(Enum):
    """Signal confidence levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class TechnicalIndicators:
    """Technical indicator values for a stock."""

    # Moving Averages
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    sma200: Optional[float] = None
    ema12: Optional[float] = None
    ema26: Optional[float] = None
    ema50: Optional[float] = None

    # RSI
    rsi14: Optional[float] = None

    # MACD
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None

    # ATR (Volatility)
    atr14: Optional[float] = None

    # Volume
    volume_sma20: Optional[float] = None
    volume_ratio: Optional[float] = None  # Current volume / Average volume

    # Price Position
    price_vs_sma20: Optional[float] = None  # Percentage above/below SMA20
    price_vs_sma50: Optional[float] = None
    price_vs_sma200: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'moving_averages': {
                'sma20': self.sma20,
                'sma50': self.sma50,
                'sma200': self.sma200,
                'ema12': self.ema12,
                'ema26': self.ema26,
                'ema50': self.ema50,
            },
            'momentum': {
                'rsi14': self.rsi14,
                'macd': self.macd,
                'macd_signal': self.macd_signal,
                'macd_histogram': self.macd_histogram,
            },
            'volatility': {
                'atr14': self.atr14,
                'bb_upper': self.bb_upper,
                'bb_middle': self.bb_middle,
                'bb_lower': self.bb_lower,
                'bb_width': self.bb_width,
            },
            'volume': {
                'volume_sma20': self.volume_sma20,
                'volume_ratio': self.volume_ratio,
            },
            'price_position': {
                'vs_sma20': self.price_vs_sma20,
                'vs_sma50': self.price_vs_sma50,
                'vs_sma200': self.price_vs_sma200,
            }
        }


@dataclass
class TechnicalScore:
    """Technical analysis score breakdown."""

    trend_score: float = 0.0  # 0-100
    momentum_score: float = 0.0  # 0-100
    volatility_score: float = 0.0  # 0-100
    volume_score: float = 0.0  # 0-100
    composite_score: float = 0.0  # 0-100

    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'trend_score': round(self.trend_score, 2),
            'momentum_score': round(self.momentum_score, 2),
            'volatility_score': round(self.volatility_score, 2),
            'volume_score': round(self.volume_score, 2),
            'composite_score': round(self.composite_score, 2),
            'reasons': self.reasons,
        }


@dataclass
class TradingSignal:
    """Trading signal with reasoning."""

    signal_type: SignalType
    confidence: ConfidenceLevel
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'signal': self.signal_type.value,
            'confidence': self.confidence.value,
            'entry_price': round(self.entry_price, 2),
            'target_price': round(self.target_price, 2) if self.target_price else None,
            'stop_loss': round(self.stop_loss, 2) if self.stop_loss else None,
            'risk_reward_ratio': round(self.risk_reward_ratio, 2) if self.risk_reward_ratio else None,
            'reasons': self.reasons,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class StockData:
    """Complete stock data with technical analysis."""

    symbol: str
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    timestamp: datetime

    # Technical Analysis
    technical_indicators: Optional[TechnicalIndicators] = None
    technical_score: Optional[TechnicalScore] = None
    trading_signal: Optional[TradingSignal] = None

    # Metadata
    market_cap: Optional[float] = None
    avg_volume_20d: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'price_data': {
                'current': round(self.current_price, 2),
                'open': round(self.open_price, 2),
                'high': round(self.high_price, 2),
                'low': round(self.low_price, 2),
                'close': round(self.close_price, 2),
                'volume': self.volume,
            },
            'technical_indicators': self.technical_indicators.to_dict() if self.technical_indicators else None,
            'technical_score': self.technical_score.to_dict() if self.technical_score else None,
            'trading_signal': self.trading_signal.to_dict() if self.trading_signal else None,
            'metadata': {
                'market_cap': self.market_cap,
                'avg_volume_20d': self.avg_volume_20d,
            },
            'timestamp': self.timestamp.isoformat(),
        }

