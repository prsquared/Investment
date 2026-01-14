"""
Technical Analysis Engine - Core calculations for swing trading.
"""
from typing import Optional, List
import pandas as pd
import numpy as np
from loguru import logger

try:
    from .models import (
        TechnicalIndicators,
        TechnicalScore,
        TradingSignal,
        SignalType,
        ConfidenceLevel,
    )
    from .config import get_config
except ImportError:
    from models import (
        TechnicalIndicators,
        TechnicalScore,
        TradingSignal,
        SignalType,
        ConfidenceLevel,
    )
    from config import get_config


class TechnicalAnalysisEngine:
    """
    Calculates technical indicators and generates trading signals.
    Optimized for swing trading (2-30 day holding periods).
    """

    def __init__(self):
        self.config = get_config().technical_analysis
        logger.info("TechnicalAnalysisEngine initialized")

    def calculate_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """
        Calculate all technical indicators from price data.

        Args:
            df: DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
               Index should be datetime.

        Returns:
            TechnicalIndicators object with all calculated values
        """
        if len(df) < self.config.min_historical_days:
            logger.warning(f"Insufficient data: {len(df)} days (need {self.config.min_historical_days})")
            return TechnicalIndicators()

        indicators = TechnicalIndicators()

        try:
            # Moving Averages
            indicators.sma20 = self._calculate_sma(df['close'], 20)
            indicators.sma50 = self._calculate_sma(df['close'], 50)
            indicators.sma200 = self._calculate_sma(df['close'], 200)

            indicators.ema12 = self._calculate_ema(df['close'], 12)
            indicators.ema26 = self._calculate_ema(df['close'], 26)
            indicators.ema50 = self._calculate_ema(df['close'], 50)

            # RSI
            indicators.rsi14 = self._calculate_rsi(df['close'], self.config.rsi_period)

            # MACD
            macd_values = self._calculate_macd(
                df['close'],
                self.config.macd_fast,
                self.config.macd_slow,
                self.config.macd_signal
            )
            indicators.macd = macd_values['macd']
            indicators.macd_signal = macd_values['signal']
            indicators.macd_histogram = macd_values['histogram']

            # Bollinger Bands
            bb_values = self._calculate_bollinger_bands(
                df['close'],
                self.config.bb_period,
                self.config.bb_std
            )
            indicators.bb_upper = bb_values['upper']
            indicators.bb_middle = bb_values['middle']
            indicators.bb_lower = bb_values['lower']
            indicators.bb_width = bb_values['width']

            # ATR (Volatility)
            indicators.atr14 = self._calculate_atr(df, self.config.atr_period)

            # Volume Analysis
            indicators.volume_sma20 = self._calculate_sma(df['volume'], self.config.volume_ma_period)
            current_volume = df['volume'].iloc[-1]
            indicators.volume_ratio = current_volume / indicators.volume_sma20 if indicators.volume_sma20 else None

            # Price Position relative to MAs
            current_price = df['close'].iloc[-1]
            if indicators.sma20:
                indicators.price_vs_sma20 = ((current_price - indicators.sma20) / indicators.sma20) * 100
            if indicators.sma50:
                indicators.price_vs_sma50 = ((current_price - indicators.sma50) / indicators.sma50) * 100
            if indicators.sma200:
                indicators.price_vs_sma200 = ((current_price - indicators.sma200) / indicators.sma200) * 100

            logger.debug(f"Calculated indicators successfully")

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")

        return indicators

    def calculate_technical_score(
        self,
        indicators: TechnicalIndicators,
        current_price: float
    ) -> TechnicalScore:
        """
        Calculate composite technical score (0-100) from indicators.

        Args:
            indicators: TechnicalIndicators object
            current_price: Current stock price

        Returns:
            TechnicalScore with breakdown and reasons
        """
        score = TechnicalScore()

        # 1. Trend Score (25%)
        trend_score, trend_reasons = self._score_trend(indicators, current_price)
        score.trend_score = trend_score
        score.reasons.extend(trend_reasons)

        # 2. Momentum Score (25%)
        momentum_score, momentum_reasons = self._score_momentum(indicators)
        score.momentum_score = momentum_score
        score.reasons.extend(momentum_reasons)

        # 3. Volatility Score (20%)
        volatility_score, volatility_reasons = self._score_volatility(indicators, current_price)
        score.volatility_score = volatility_score
        score.reasons.extend(volatility_reasons)

        # 4. Volume Score (30%)
        volume_score, volume_reasons = self._score_volume(indicators)
        score.volume_score = volume_score
        score.reasons.extend(volume_reasons)

        # Calculate weighted composite score
        score.composite_score = (
            (trend_score * self.config.weight_trend / 100) +
            (momentum_score * self.config.weight_momentum / 100) +
            (volatility_score * self.config.weight_volatility / 100) +
            (volume_score * self.config.weight_volume / 100)
        )

        logger.info(f"Technical Score: {score.composite_score:.2f} "
                   f"(Trend: {trend_score:.1f}, Momentum: {momentum_score:.1f}, "
                   f"Volatility: {volatility_score:.1f}, Volume: {volume_score:.1f})")

        return score

    def generate_signal(
        self,
        indicators: TechnicalIndicators,
        score: TechnicalScore,
        current_price: float
    ) -> TradingSignal:
        """
        Generate trading signal based on technical analysis.

        Args:
            indicators: TechnicalIndicators object
            score: TechnicalScore object
            current_price: Current stock price

        Returns:
            TradingSignal with entry, target, stop-loss
        """
        signal_reasons = []
        signal_type = SignalType.HOLD
        confidence = ConfidenceLevel.LOW

        # Determine signal based on composite score and key indicators
        if score.composite_score >= 70:
            signal_type = SignalType.BUY
            confidence = ConfidenceLevel.HIGH if score.composite_score >= 80 else ConfidenceLevel.MEDIUM
            signal_reasons.append(f"Strong technical score: {score.composite_score:.1f}/100")

        elif score.composite_score >= 55:
            signal_type = SignalType.BUY
            confidence = ConfidenceLevel.MEDIUM if score.composite_score >= 60 else ConfidenceLevel.LOW
            signal_reasons.append(f"Moderate technical score: {score.composite_score:.1f}/100")

        elif score.composite_score <= 30:
            signal_type = SignalType.SELL
            confidence = ConfidenceLevel.HIGH if score.composite_score <= 20 else ConfidenceLevel.MEDIUM
            signal_reasons.append(f"Weak technical score: {score.composite_score:.1f}/100")

        else:
            signal_type = SignalType.HOLD
            signal_reasons.append(f"Neutral technical score: {score.composite_score:.1f}/100")

        # Calculate target and stop-loss based on ATR
        target_price = None
        stop_loss = None

        if signal_type == SignalType.BUY and indicators.atr14:
            # Target: 2-3x ATR above current price (for swing trading)
            atr_multiplier = 2.5 if confidence == ConfidenceLevel.HIGH else 2.0
            target_price = current_price + (indicators.atr14 * atr_multiplier)

            # Stop-loss: 1-1.5x ATR below current price
            stop_multiplier = 1.0 if confidence == ConfidenceLevel.HIGH else 1.5
            stop_loss = current_price - (indicators.atr14 * stop_multiplier)

            signal_reasons.append(f"Target: ${target_price:.2f}, Stop: ${stop_loss:.2f} (ATR-based)")

        elif signal_type == SignalType.SELL and indicators.atr14:
            # For sell signals, reverse the logic
            target_price = current_price - (indicators.atr14 * 2.0)
            stop_loss = current_price + (indicators.atr14 * 1.0)

        # Add specific indicator reasons
        signal_reasons.extend(score.reasons[:3])  # Add top 3 reasons from score

        signal = TradingSignal(
            signal_type=signal_type,
            confidence=confidence,
            entry_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            reasons=signal_reasons
        )

        logger.info(f"Signal: {signal_type.value} ({confidence.value}) @ ${current_price:.2f}")

        return signal

    # =====================================================================
    # Private Helper Methods - Indicator Calculations
    # =====================================================================

    def _calculate_sma(self, series: pd.Series, period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(series) < period:
            return None
        return float(series.rolling(window=period).mean().iloc[-1])

    def _calculate_ema(self, series: pd.Series, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(series) < period:
            return None
        return float(series.ewm(span=period, adjust=False).mean().iloc[-1])

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if len(series) < period + 1:
            return None

        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])

    def _calculate_macd(
        self,
        series: pd.Series,
        fast: int,
        slow: int,
        signal: int
    ) -> dict:
        """Calculate MACD indicator."""
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }

    def _calculate_bollinger_bands(
        self,
        series: pd.Series,
        period: int,
        std_dev: float
    ) -> dict:
        """Calculate Bollinger Bands."""
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        width = ((upper - lower) / sma) * 100  # Width as percentage

        return {
            'upper': float(upper.iloc[-1]),
            'middle': float(sma.iloc[-1]),
            'lower': float(lower.iloc[-1]),
            'width': float(width.iloc[-1])
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Average True Range."""
        if len(df) < period + 1:
            return None

        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return float(atr.iloc[-1])

    # =====================================================================
    # Private Helper Methods - Scoring
    # =====================================================================

    def _score_trend(self, indicators: TechnicalIndicators, current_price: float) -> tuple[float, List[str]]:
        """Score trend strength (0-100)."""
        score = 50.0  # Neutral
        reasons = []

        # Check MA alignment (golden cross pattern)
        if all([indicators.sma20, indicators.sma50, indicators.sma200]):
            if indicators.sma20 > indicators.sma50 > indicators.sma200:
                score += 30
                reasons.append("Bullish MA alignment (SMA20 > SMA50 > SMA200)")
            elif indicators.sma20 < indicators.sma50 < indicators.sma200:
                score -= 30
                reasons.append("Bearish MA alignment (SMA20 < SMA50 < SMA200)")

        # Price position relative to key MAs
        if indicators.price_vs_sma50 is not None:
            if indicators.price_vs_sma50 > 5:
                score += 10
                reasons.append(f"Price {indicators.price_vs_sma50:.1f}% above SMA50")
            elif indicators.price_vs_sma50 < -5:
                score -= 10
                reasons.append(f"Price {abs(indicators.price_vs_sma50):.1f}% below SMA50")

        # EMA crossover
        if indicators.ema12 and indicators.ema26:
            if indicators.ema12 > indicators.ema26:
                score += 10
                reasons.append("Bullish EMA crossover (EMA12 > EMA26)")
            else:
                score -= 10

        return max(0, min(100, score)), reasons

    def _score_momentum(self, indicators: TechnicalIndicators) -> tuple[float, List[str]]:
        """Score momentum strength (0-100)."""
        score = 50.0  # Neutral
        reasons = []

        # RSI analysis
        if indicators.rsi14 is not None:
            if 40 <= indicators.rsi14 <= 60:
                score += 20
                reasons.append(f"RSI neutral: {indicators.rsi14:.1f}")
            elif indicators.rsi14 > 70:
                score -= 20
                reasons.append(f"RSI overbought: {indicators.rsi14:.1f}")
            elif indicators.rsi14 < 30:
                score += 15  # Oversold can be bullish for swing trading
                reasons.append(f"RSI oversold (potential reversal): {indicators.rsi14:.1f}")
            elif 50 < indicators.rsi14 < 70:
                score += 10
                reasons.append(f"RSI bullish: {indicators.rsi14:.1f}")

        # MACD analysis
        if indicators.macd_histogram is not None:
            if indicators.macd_histogram > 0:
                score += 15
                reasons.append("MACD histogram positive")
            else:
                score -= 15
                reasons.append("MACD histogram negative")

        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal:
                score += 15
                reasons.append("MACD bullish crossover")

        return max(0, min(100, score)), reasons

    def _score_volatility(
        self,
        indicators: TechnicalIndicators,
        current_price: float
    ) -> tuple[float, List[str]]:
        """Score volatility conditions (0-100). Higher score = favorable volatility for swing trading."""
        score = 50.0
        reasons = []

        # Bollinger Band position
        if all([indicators.bb_upper, indicators.bb_lower, indicators.bb_middle]):
            bb_range = indicators.bb_upper - indicators.bb_lower
            position = (current_price - indicators.bb_lower) / bb_range if bb_range > 0 else 0.5

            if 0.3 <= position <= 0.7:
                score += 20
                reasons.append("Price in middle BB range (stable)")
            elif position < 0.2:
                score += 15
                reasons.append("Price near lower BB (potential bounce)")
            elif position > 0.8:
                score -= 15
                reasons.append("Price near upper BB (potential pullback)")

        # ATR-based volatility (moderate volatility is good for swing trading)
        if indicators.atr14 and current_price > 0:
            atr_percent = (indicators.atr14 / current_price) * 100
            if 2 <= atr_percent <= 5:  # Sweet spot for swing trading
                score += 30
                reasons.append(f"Ideal volatility: {atr_percent:.1f}%")
            elif atr_percent < 2:
                score += 10
                reasons.append(f"Low volatility: {atr_percent:.1f}%")
            elif atr_percent > 8:
                score -= 20
                reasons.append(f"High volatility: {atr_percent:.1f}%")

        return max(0, min(100, score)), reasons

    def _score_volume(self, indicators: TechnicalIndicators) -> tuple[float, List[str]]:
        """Score volume conditions (0-100)."""
        score = 50.0
        reasons = []

        # Volume ratio analysis
        if indicators.volume_ratio is not None:
            if indicators.volume_ratio > self.config.volume_spike_threshold:
                score += 40
                reasons.append(f"Volume spike: {indicators.volume_ratio:.1f}x average")
            elif indicators.volume_ratio > 1.2:
                score += 25
                reasons.append(f"Above average volume: {indicators.volume_ratio:.1f}x")
            elif indicators.volume_ratio < 0.5:
                score -= 30
                reasons.append(f"Low volume: {indicators.volume_ratio:.1f}x average")
            else:
                score += 10
                reasons.append(f"Normal volume: {indicators.volume_ratio:.1f}x")

        return max(0, min(100, score)), reasons

