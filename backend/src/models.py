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
class FundamentalIndicators:
    """Fundamental analysis metrics for a stock."""

    # Valuation Ratios
    pe_ratio: Optional[float] = None  # Price-to-Earnings
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None  # P/E to Growth
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    ev_to_ebitda: Optional[float] = None

    # Growth Metrics
    earnings_growth: Optional[float] = None  # YoY EPS growth %
    revenue_growth: Optional[float] = None  # YoY revenue growth %
    earnings_quarterly_growth: Optional[float] = None

    # Profitability
    profit_margin: Optional[float] = None  # Net margin %
    operating_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    roe: Optional[float] = None  # Return on Equity %
    roa: Optional[float] = None  # Return on Assets %

    # Financial Health
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    free_cash_flow: Optional[float] = None

    # Earnings & Dividends
    eps: Optional[float] = None  # Earnings per share
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None

    # Market Data
    market_cap: Optional[float] = None
    beta: Optional[float] = None  # Volatility vs market
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None

    # Analyst Data
    target_price: Optional[float] = None
    recommendation: Optional[str] = None  # Buy, Hold, Sell
    num_analysts: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'valuation': {
                'pe_ratio': self.pe_ratio,
                'forward_pe': self.forward_pe,
                'peg_ratio': self.peg_ratio,
                'price_to_book': self.price_to_book,
                'price_to_sales': self.price_to_sales,
                'ev_to_ebitda': self.ev_to_ebitda,
            },
            'growth': {
                'earnings_growth': self.earnings_growth,
                'revenue_growth': self.revenue_growth,
                'earnings_quarterly_growth': self.earnings_quarterly_growth,
            },
            'profitability': {
                'profit_margin': self.profit_margin,
                'operating_margin': self.operating_margin,
                'gross_margin': self.gross_margin,
                'roe': self.roe,
                'roa': self.roa,
            },
            'financial_health': {
                'debt_to_equity': self.debt_to_equity,
                'current_ratio': self.current_ratio,
                'quick_ratio': self.quick_ratio,
                'free_cash_flow': self.free_cash_flow,
            },
            'earnings_dividends': {
                'eps': self.eps,
                'dividend_yield': self.dividend_yield,
                'payout_ratio': self.payout_ratio,
            },
            'market': {
                'market_cap': self.market_cap,
                'beta': self.beta,
                'shares_outstanding': self.shares_outstanding,
                'float_shares': self.float_shares,
            },
            'analyst': {
                'target_price': self.target_price,
                'recommendation': self.recommendation,
                'num_analysts': self.num_analysts,
            }
        }


@dataclass
class FundamentalScore:
    """Fundamental analysis score breakdown."""

    valuation_score: float = 0.0  # 0-100 (lower P/E, PEG is better)
    growth_score: float = 0.0  # 0-100 (higher growth is better)
    profitability_score: float = 0.0  # 0-100 (higher margins, ROE is better)
    financial_health_score: float = 0.0  # 0-100 (lower debt, higher liquidity is better)
    composite_score: float = 0.0  # 0-100

    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'valuation_score': round(self.valuation_score, 2),
            'growth_score': round(self.growth_score, 2),
            'profitability_score': round(self.profitability_score, 2),
            'financial_health_score': round(self.financial_health_score, 2),
            'composite_score': round(self.composite_score, 2),
            'reasons': self.reasons,
        }


@dataclass
class StockData:
    """Complete stock data with technical and fundamental analysis."""

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
    
    # Fundamental Analysis
    fundamental_indicators: Optional[FundamentalIndicators] = None
    fundamental_score: Optional[FundamentalScore] = None
    
    # Combined Signal
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
            'fundamental_indicators': self.fundamental_indicators.to_dict() if self.fundamental_indicators else None,
            'fundamental_score': self.fundamental_score.to_dict() if self.fundamental_score else None,
            'trading_signal': self.trading_signal.to_dict() if self.trading_signal else None,
            'metadata': {
                'market_cap': self.market_cap,
                'avg_volume_20d': self.avg_volume_20d,
            },
            'timestamp': self.timestamp.isoformat(),
        }

