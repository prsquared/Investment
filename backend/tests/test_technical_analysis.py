"""
Unit tests for Technical Analysis Engine.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from technical_analysis import TechnicalAnalysisEngine
from models import TechnicalIndicators, SignalType, ConfidenceLevel


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')

    # Generate realistic price movement
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(250) * 2)

    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(250) * 0.01),
        'high': close_prices * (1 + abs(np.random.randn(250)) * 0.02),
        'low': close_prices * (1 - abs(np.random.randn(250)) * 0.02),
        'close': close_prices,
        'volume': np.random.randint(1_000_000, 10_000_000, 250)
    }, index=dates)

    return df


@pytest.fixture
def bullish_trend_data():
    """Generate data showing a bullish trend."""
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')

    # Upward trending prices
    close_prices = np.linspace(100, 150, 250) + np.random.randn(250) * 1

    df = pd.DataFrame({
        'open': close_prices * 0.99,
        'high': close_prices * 1.01,
        'low': close_prices * 0.98,
        'close': close_prices,
        'volume': np.random.randint(2_000_000, 15_000_000, 250)
    }, index=dates)

    return df


@pytest.fixture
def bearish_trend_data():
    """Generate data showing a bearish trend."""
    dates = pd.date_range(end=datetime.now(), periods=250, freq='D')

    # Downward trending prices
    close_prices = np.linspace(150, 100, 250) + np.random.randn(250) * 1

    df = pd.DataFrame({
        'open': close_prices * 1.01,
        'high': close_prices * 1.02,
        'low': close_prices * 0.99,
        'close': close_prices,
        'volume': np.random.randint(500_000, 3_000_000, 250)
    }, index=dates)

    return df


class TestTechnicalAnalysisEngine:
    """Test suite for TechnicalAnalysisEngine."""

    def test_initialization(self):
        """Test engine initialization."""
        engine = TechnicalAnalysisEngine()
        assert engine is not None
        assert engine.config is not None

    def test_calculate_sma(self, sample_price_data):
        """Test SMA calculation."""
        engine = TechnicalAnalysisEngine()

        sma20 = engine._calculate_sma(sample_price_data['close'], 20)
        assert sma20 is not None
        assert isinstance(sma20, float)
        assert sma20 > 0

    def test_calculate_ema(self, sample_price_data):
        """Test EMA calculation."""
        engine = TechnicalAnalysisEngine()

        ema12 = engine._calculate_ema(sample_price_data['close'], 12)
        assert ema12 is not None
        assert isinstance(ema12, float)
        assert ema12 > 0

    def test_calculate_rsi(self, sample_price_data):
        """Test RSI calculation."""
        engine = TechnicalAnalysisEngine()

        rsi = engine._calculate_rsi(sample_price_data['close'], 14)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_calculate_macd(self, sample_price_data):
        """Test MACD calculation."""
        engine = TechnicalAnalysisEngine()

        macd = engine._calculate_macd(sample_price_data['close'], 12, 26, 9)
        assert 'macd' in macd
        assert 'signal' in macd
        assert 'histogram' in macd
        assert all(isinstance(v, float) for v in macd.values())

    def test_calculate_bollinger_bands(self, sample_price_data):
        """Test Bollinger Bands calculation."""
        engine = TechnicalAnalysisEngine()

        bb = engine._calculate_bollinger_bands(sample_price_data['close'], 20, 2.0)
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        assert 'width' in bb
        assert bb['upper'] > bb['middle'] > bb['lower']

    def test_calculate_atr(self, sample_price_data):
        """Test ATR calculation."""
        engine = TechnicalAnalysisEngine()

        atr = engine._calculate_atr(sample_price_data, 14)
        assert atr is not None
        assert isinstance(atr, float)
        assert atr > 0

    def test_calculate_indicators_complete(self, sample_price_data):
        """Test complete indicator calculation."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(sample_price_data)

        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.sma20 is not None
        assert indicators.sma50 is not None
        assert indicators.sma200 is not None
        assert indicators.rsi14 is not None
        assert indicators.macd is not None
        assert indicators.atr14 is not None

    def test_calculate_indicators_insufficient_data(self):
        """Test indicator calculation with insufficient data."""
        engine = TechnicalAnalysisEngine()

        # Create small dataset
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        df = pd.DataFrame({
            'open': [100] * 50,
            'high': [105] * 50,
            'low': [95] * 50,
            'close': [100] * 50,
            'volume': [1_000_000] * 50
        }, index=dates)

        indicators = engine.calculate_indicators(df)
        # Should return empty indicators due to insufficient data
        assert indicators.sma200 is None

    def test_score_trend_bullish(self, bullish_trend_data):
        """Test trend scoring with bullish data."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]

        score, reasons = engine._score_trend(indicators, current_price)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score > 50  # Should be bullish
        assert isinstance(reasons, list)

    def test_score_trend_bearish(self, bearish_trend_data):
        """Test trend scoring with bearish data."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bearish_trend_data)
        current_price = bearish_trend_data['close'].iloc[-1]

        score, reasons = engine._score_trend(indicators, current_price)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert score < 50  # Should be bearish

    def test_score_momentum(self, sample_price_data):
        """Test momentum scoring."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(sample_price_data)
        score, reasons = engine._score_momentum(indicators)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert isinstance(reasons, list)

    def test_score_volatility(self, sample_price_data):
        """Test volatility scoring."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(sample_price_data)
        current_price = sample_price_data['close'].iloc[-1]

        score, reasons = engine._score_volatility(indicators, current_price)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert isinstance(reasons, list)

    def test_score_volume(self, sample_price_data):
        """Test volume scoring."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(sample_price_data)
        score, reasons = engine._score_volume(indicators)

        assert isinstance(score, float)
        assert 0 <= score <= 100
        assert isinstance(reasons, list)

    def test_calculate_technical_score(self, bullish_trend_data):
        """Test composite technical score calculation."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]

        score = engine.calculate_technical_score(indicators, current_price)

        assert score.trend_score >= 0
        assert score.momentum_score >= 0
        assert score.volatility_score >= 0
        assert score.volume_score >= 0
        assert score.composite_score >= 0
        assert score.composite_score <= 100
        assert isinstance(score.reasons, list)
        assert len(score.reasons) > 0

    def test_generate_signal_bullish(self, bullish_trend_data):
        """Test signal generation for bullish data."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]
        score = engine.calculate_technical_score(indicators, current_price)

        signal = engine.generate_signal(indicators, score, current_price)

        assert signal.signal_type in [SignalType.BUY, SignalType.HOLD, SignalType.SELL]
        assert signal.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert signal.entry_price == current_price
        assert isinstance(signal.reasons, list)
        assert len(signal.reasons) > 0

    def test_generate_signal_with_targets(self, bullish_trend_data):
        """Test that BUY signals include target and stop-loss."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]

        # Force high score to get BUY signal
        score = engine.calculate_technical_score(indicators, current_price)
        score.composite_score = 75  # Force high score

        signal = engine.generate_signal(indicators, score, current_price)

        if signal.signal_type == SignalType.BUY:
            assert signal.target_price is not None
            assert signal.stop_loss is not None
            assert signal.target_price > signal.entry_price
            assert signal.stop_loss < signal.entry_price

    def test_indicators_to_dict(self, sample_price_data):
        """Test indicators serialization to dict."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(sample_price_data)
        result = indicators.to_dict()

        assert isinstance(result, dict)
        assert 'moving_averages' in result
        assert 'momentum' in result
        assert 'volatility' in result
        assert 'volume' in result

    def test_score_to_dict(self, bullish_trend_data):
        """Test score serialization to dict."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]
        score = engine.calculate_technical_score(indicators, current_price)

        result = score.to_dict()

        assert isinstance(result, dict)
        assert 'trend_score' in result
        assert 'momentum_score' in result
        assert 'composite_score' in result
        assert 'reasons' in result

    def test_signal_to_dict(self, bullish_trend_data):
        """Test signal serialization to dict."""
        engine = TechnicalAnalysisEngine()

        indicators = engine.calculate_indicators(bullish_trend_data)
        current_price = bullish_trend_data['close'].iloc[-1]
        score = engine.calculate_technical_score(indicators, current_price)
        signal = engine.generate_signal(indicators, score, current_price)

        result = signal.to_dict()

        assert isinstance(result, dict)
        assert 'signal' in result
        assert 'confidence' in result
        assert 'entry_price' in result
        assert 'reasons' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

