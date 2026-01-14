# Stock Selection Backend - Technical Analysis Module

## Overview

This backend module implements **Technical Analysis** for swing trading in the US stock market. It calculates technical indicators, scores stocks, and generates actionable trading signals for 2-30 day holding periods.

## Features

### ✅ Technical Indicators
- **Moving Averages**: SMA(20, 50, 200), EMA(12, 26, 50)
- **Momentum**: RSI(14), MACD (12, 26, 9)
- **Volatility**: Bollinger Bands, ATR(14)
- **Volume**: Volume ratio, volume spikes
- **Price Position**: Relative to key moving averages

### ✅ Scoring System
- **Trend Score** (0-100): MA alignment, crossovers
- **Momentum Score** (0-100): RSI, MACD signals
- **Volatility Score** (0-100): BB position, ATR analysis
- **Volume Score** (0-100): Volume ratio, spikes
- **Composite Score** (0-100): Weighted combination

### ✅ Signal Generation
- **BUY/SELL/HOLD** signals with confidence levels (HIGH/MEDIUM/LOW)
- **Entry price**, **target price**, **stop-loss** levels
- **Risk/Reward ratio** calculation
- **Detailed reasoning** for each signal

### ✅ Data Sources
- Yahoo Finance (via yfinance) - Free, no API key required
- Support for Alpha Vantage, Polygon.io, Finnhub (configurable)

## Project Structure

```
backend/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── config.py                # Configuration management
│   ├── models.py                # Data models (StockData, TechnicalIndicators, etc.)
│   ├── technical_analysis.py   # Technical analysis engine
│   └── data_fetcher.py          # Data fetching utilities
├── examples/
│   └── technical_analysis_example.py  # Complete workflow example
├── tests/
│   └── test_technical_analysis.py     # Unit tests
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup Steps

1. **Navigate to backend directory**:
   ```powershell
   cd C:\workspace\StockSelection\Investment\backend
   ```

2. **Create virtual environment** (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   ```powershell
   cp .env.example .env
   # Edit .env with your API keys if using paid data sources
   ```

5. **Create necessary directories**:
   ```powershell
   mkdir logs, output
   ```

## Quick Start

### Example 1: Analyze a Single Stock

```python
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalysisEngine
from src.config import get_config

# Initialize
fetcher = DataFetcher()
analyzer = TechnicalAnalysisEngine()
config = get_config()

# Fetch data
symbol = "AAPL"
historical_df = fetcher.fetch_historical_data(symbol, days=250)
current_data = fetcher.fetch_current_price(symbol)

# Calculate indicators
indicators = analyzer.calculate_indicators(historical_df)

# Calculate score
score = analyzer.calculate_technical_score(
    indicators,
    current_data['current_price']
)

# Generate signal
signal = analyzer.generate_signal(
    indicators,
    score,
    current_data['current_price']
)

print(f"Signal: {signal.signal_type.value} ({signal.confidence.value})")
print(f"Score: {score.composite_score:.1f}/100")
print(f"Entry: ${signal.entry_price:.2f}")
print(f"Target: ${signal.target_price:.2f}")
print(f"Stop Loss: ${signal.stop_loss:.2f}")
```

### Example 2: Run Complete Example Script

```powershell
python examples/technical_analysis_example.py
```

This will:
1. Analyze AAPL in detail
2. Analyze multiple stocks (AAPL, MSFT, GOOGL, TSLA, NVDA)
3. Rank them by technical score
4. Generate trading signals
5. Save results to `output/` directory

## Configuration

### Technical Analysis Parameters

Edit `src/config.py` or set environment variables:

```python
# Moving Average Periods
sma_periods = [20, 50, 200]
ema_periods = [12, 26, 50]

# RSI Settings
rsi_period = 14
rsi_overbought = 70.0
rsi_oversold = 30.0

# MACD Settings
macd_fast = 12
macd_slow = 26
macd_signal = 9

# Scoring Weights (must sum to 100)
weight_trend = 25.0
weight_momentum = 25.0
weight_volatility = 20.0
weight_volume = 30.0
```

### Stock Filtering

```python
# Minimum requirements
min_price = 5.0              # Avoid penny stocks
min_volume = 500_000         # Daily volume
min_market_cap = 1_000_000_000  # $1B minimum
```

## Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_technical_analysis.py -v
```

## API Reference

### TechnicalAnalysisEngine

Main engine for technical analysis calculations.

#### Methods

**`calculate_indicators(df: pd.DataFrame) -> TechnicalIndicators`**
- Calculate all technical indicators from price data
- Requires DataFrame with columns: `open, high, low, close, volume`
- Returns `TechnicalIndicators` object

**`calculate_technical_score(indicators: TechnicalIndicators, current_price: float) -> TechnicalScore`**
- Calculate composite technical score (0-100)
- Returns breakdown by category and reasoning

**`generate_signal(indicators: TechnicalIndicators, score: TechnicalScore, current_price: float) -> TradingSignal`**
- Generate BUY/SELL/HOLD signal
- Includes confidence level, targets, stop-loss

### DataFetcher

Fetch stock market data from various sources.

#### Methods

**`fetch_historical_data(symbol: str, days: int = 365) -> pd.DataFrame`**
- Fetch historical OHLCV data
- Automatically adjusts for splits/dividends

**`fetch_current_price(symbol: str) -> dict`**
- Get current price and basic info
- Returns dict with price, volume, market cap

**`fetch_multiple_symbols(symbols: List[str], days: int = 365) -> dict`**
- Batch fetch data for multiple symbols
- Returns dict mapping symbol to DataFrame

## Data Models

### StockData
Complete stock information including technical analysis.

```python
@dataclass
class StockData:
    symbol: str
    current_price: float
    volume: int
    technical_indicators: TechnicalIndicators
    technical_score: TechnicalScore
    trading_signal: TradingSignal
    # ... more fields
```

### TechnicalIndicators
All calculated technical indicators.

```python
@dataclass
class TechnicalIndicators:
    sma20, sma50, sma200: float
    ema12, ema26, ema50: float
    rsi14: float
    macd, macd_signal, macd_histogram: float
    bb_upper, bb_middle, bb_lower: float
    atr14: float
    volume_ratio: float
    # ... more fields
```

### TradingSignal
Trading signal with actionable information.

```python
@dataclass
class TradingSignal:
    signal_type: SignalType  # BUY, SELL, HOLD
    confidence: ConfidenceLevel  # HIGH, MEDIUM, LOW
    entry_price: float
    target_price: float
    stop_loss: float
    reasons: List[str]
```

## Scoring Methodology

### Composite Score Calculation

```
Composite Score = 
  (Trend Score × 25%) +
  (Momentum Score × 25%) +
  (Volatility Score × 20%) +
  (Volume Score × 30%)
```

### Signal Generation Rules

- **BUY Signal**: Composite score ≥ 55
  - HIGH confidence: ≥ 80
  - MEDIUM confidence: 70-79
  - LOW confidence: 55-69

- **SELL Signal**: Composite score ≤ 30
  - HIGH confidence: ≤ 20
  - MEDIUM confidence: 21-30

- **HOLD Signal**: Composite score 31-54

### Target & Stop-Loss Calculation

Based on ATR (Average True Range):
- **Target Price**: Entry + (2-3 × ATR)
- **Stop Loss**: Entry - (1-1.5 × ATR)
- Typical Risk/Reward ratio: 1:2 or better

## Best Practices

### 1. Data Quality
```python
# Always validate data before analysis
if df is None or len(df) < 200:
    logger.warning("Insufficient data")
    return None
```

### 2. Error Handling
```python
try:
    indicators = analyzer.calculate_indicators(df)
except Exception as e:
    logger.error(f"Error: {e}")
    # Handle gracefully
```

### 3. Rate Limiting
```python
# Respect API rate limits
time.sleep(config.api_call_delay)  # Default: 0.2 seconds
```

### 4. Caching
```python
# Cache expensive calculations
# Store historical data locally
# Use database for production
```

## Performance Considerations

- **Parallel Processing**: Use multiprocessing for analyzing multiple stocks
- **Batch Requests**: Fetch data in batches when possible
- **Incremental Updates**: Only fetch new data, not full history
- **Database Indexing**: Index by symbol and date

## Logging

Logs are stored in `logs/` directory:
- `technical_analysis.log`: Detailed analysis logs
- Rotation: Daily
- Retention: 7 days

Log levels:
- **DEBUG**: Detailed calculation steps
- **INFO**: Analysis progress and results
- **WARNING**: Data quality issues
- **ERROR**: Calculation errors

## Troubleshooting

### Issue: "Insufficient historical data"
**Solution**: Increase `days` parameter or check if stock is newly listed

### Issue: "No data returned"
**Solution**: Verify symbol is correct and stock is actively traded

### Issue: "Rate limit exceeded"
**Solution**: Increase `api_call_delay` in config or use paid API tier

### Issue: "Module not found"
**Solution**: Ensure virtual environment is activated and dependencies installed

## Roadmap

- [ ] Add more technical indicators (Stochastic, OBV, etc.)
- [ ] Implement chart pattern recognition
- [ ] Add support/resistance level detection
- [ ] Machine learning for signal optimization
- [ ] Real-time WebSocket data feeds
- [ ] PostgreSQL/MongoDB integration
- [ ] REST API endpoints
- [ ] Backtesting framework

## Contributing

1. Write tests for new features
2. Follow PEP 8 style guidelines
3. Add docstrings to all functions
4. Update README with new features

## Disclaimer

⚠️ **This software is for educational and research purposes only.**

- Not financial advice
- No guarantee of returns
- Past performance ≠ future results
- Always do your own research
- Consider consulting a financial advisor

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check existing documentation
- Review example code

---

**Happy Trading! 📈🚀**

