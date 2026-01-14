# Technical Analysis Module - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECHNICAL ANALYSIS MODULE                     │
│                  (Swing Trading - US Market)                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  DataFetcher (data_fetcher.py)                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐  │
│  │ Yahoo Finance│      │ Alpha Vantage│      │  Polygon.io  │  │
│  │   (yfinance) │ ---> │   (optional) │ ---> │  (optional)  │  │
│  └──────────────┘      └──────────────┘      └──────────────┘  │
│         │                                                        │
│         ├─> Historical Data (OHLCV, 250+ days)                 │
│         ├─> Current Price & Volume                              │
│         └─> Stock Info (Market Cap, Sector)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ANALYSIS LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  TechnicalAnalysisEngine (technical_analysis.py)                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  INDICATOR CALCULATIONS                                 │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Moving Averages    │ SMA(20, 50, 200)                 │    │
│  │                     │ EMA(12, 26, 50)                  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Momentum          │ RSI(14) - Overbought/Oversold     │    │
│  │                     │ MACD(12,26,9) - Trend & Momentum │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Volatility        │ Bollinger Bands(20, 2σ)           │    │
│  │                     │ ATR(14) - Average True Range     │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Volume            │ Volume Ratio (vs 20-day avg)      │    │
│  │                     │ Volume Spikes (>2x)              │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  SCORING SYSTEM (0-100)                                 │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Trend Score       │ 25% │ MA alignment, crossovers   │    │
│  │  Momentum Score    │ 25% │ RSI, MACD signals          │    │
│  │  Volatility Score  │ 20% │ BB position, ATR %         │    │
│  │  Volume Score      │ 30% │ Volume ratio, spikes       │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Composite Score = Weighted Average                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  SIGNAL GENERATION                                      │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Score ≥ 80  │ Strong BUY    │ High Confidence        │    │
│  │  Score 70-79 │ BUY           │ Medium Confidence      │    │
│  │  Score 55-69 │ BUY           │ Low Confidence         │    │
│  │  Score 31-54 │ HOLD          │ Neutral                │    │
│  │  Score 21-30 │ SELL          │ Medium Confidence      │    │
│  │  Score ≤ 20  │ Strong SELL   │ High Confidence        │    │
│  └────────────────────────────────────────────────────────┘    │
│                              │                                  │
│                              ▼                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  RISK MANAGEMENT                                        │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Entry Price    │ Current market price                 │    │
│  │  Target Price   │ Entry + (2-3 × ATR)                  │    │
│  │  Stop Loss      │ Entry - (1-1.5 × ATR)                │    │
│  │  Risk/Reward    │ Minimum 1:2 ratio                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA MODELS                                │
├─────────────────────────────────────────────────────────────────┤
│  models.py                                                       │
│                                                                  │
│  StockData                TechnicalIndicators                   │
│  ├─ Symbol               ├─ SMA20, SMA50, SMA200                │
│  ├─ Price Data           ├─ EMA12, EMA26, EMA50                 │
│  ├─ Volume               ├─ RSI14                               │
│  ├─ Technical Indicators ├─ MACD, Signal, Histogram             │
│  ├─ Technical Score      ├─ BB Upper/Middle/Lower               │
│  └─ Trading Signal       ├─ ATR14                               │
│                          └─ Volume Ratio                         │
│  TechnicalScore                                                  │
│  ├─ Trend Score          TradingSignal                          │
│  ├─ Momentum Score       ├─ Signal Type (BUY/SELL/HOLD)         │
│  ├─ Volatility Score     ├─ Confidence (HIGH/MEDIUM/LOW)        │
│  ├─ Volume Score         ├─ Entry Price                         │
│  ├─ Composite Score      ├─ Target Price                        │
│  └─ Reasons (list)       ├─ Stop Loss                           │
│                          └─ Reasons (list)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ JSON Output  │  │   Logging    │  │   Reports    │          │
│  │  (Detailed)  │  │  (Debug/Info)│  │  (Rankings)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  output/*.json      logs/*.log     console output               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  config.py                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ TechnicalAnalysisConfig                                   │  │
│  │  ├─ Indicator Periods (SMA, EMA, RSI, MACD, etc.)        │  │
│  │  ├─ Thresholds (RSI overbought/oversold)                 │  │
│  │  ├─ Scoring Weights (Trend 25%, Momentum 25%, etc.)      │  │
│  │  └─ Historical Data Requirements (200+ days)             │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ DataSourceConfig                                          │  │
│  │  ├─ API Keys (Alpha Vantage, Polygon, Finnhub)          │  │
│  │  ├─ Rate Limiting (0.2s delay)                           │  │
│  │  ├─ Cache Settings (24h expiry)                          │  │
│  │  └─ Retry Logic (3 attempts)                             │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ AppConfig                                                 │  │
│  │  ├─ Stock Filters (min price $5, min volume 500K)        │  │
│  │  ├─ Logging Level (INFO/DEBUG)                           │  │
│  │  └─ General Settings                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────┐
│ Stock    │
│ Symbol   │
│ (AAPL)   │
└────┬─────┘
     │
     ▼
┌──────────────────┐
│ Fetch Historical │ 
│ Data (250 days)  │ ◄── Yahoo Finance API
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ Calculate        │
│ 15+ Indicators   │
└────┬─────────────┘
     │
     ├──► Moving Averages
     ├──► RSI, MACD
     ├──► Bollinger Bands
     ├──► ATR
     └──► Volume Analysis
          │
          ▼
     ┌────────────────┐
     │ Score Each     │
     │ Category       │
     └────┬───────────┘
          │
          ├──► Trend Score (25%)
          ├──► Momentum Score (25%)
          ├──► Volatility Score (20%)
          └──► Volume Score (30%)
               │
               ▼
          ┌────────────────┐
          │ Composite Score│
          │   (0-100)      │
          └────┬───────────┘
               │
               ▼
          ┌────────────────┐
          │ Generate Signal│
          └────┬───────────┘
               │
               ├──► BUY/SELL/HOLD
               ├──► Confidence Level
               ├──► Entry Price
               ├──► Target Price
               ├──► Stop Loss
               └──► Detailed Reasons
                    │
                    ▼
               ┌─────────────┐
               │ JSON Output │
               │ + Logs      │
               └─────────────┘
```

## Component Interactions

```
┌──────────────────────────────────────────────────────────┐
│                    Example Workflow                       │
└──────────────────────────────────────────────────────────┘

1. User/System provides symbol: "AAPL"
                │
                ▼
2. DataFetcher.fetch_historical_data("AAPL", 250)
                │
                ├──> API Call to Yahoo Finance
                ├──> Returns DataFrame (250 × 5 columns)
                └──> Validates data quality
                │
                ▼
3. TechnicalAnalysisEngine.calculate_indicators(df)
                │
                ├──> _calculate_sma(close, [20,50,200])
                ├──> _calculate_ema(close, [12,26,50])
                ├──> _calculate_rsi(close, 14)
                ├──> _calculate_macd(close, 12, 26, 9)
                ├──> _calculate_bollinger_bands(close, 20, 2)
                ├──> _calculate_atr(df, 14)
                └──> Calculate volume metrics
                │
                ▼
4. Returns TechnicalIndicators object
   {sma20: 180.25, rsi14: 58.5, macd: 2.35, ...}
                │
                ▼
5. TechnicalAnalysisEngine.calculate_technical_score(indicators, 182.50)
                │
                ├──> _score_trend() → 85.0
                ├──> _score_momentum() → 70.0
                ├──> _score_volatility() → 75.0
                ├──> _score_volume() → 70.0
                └──> Composite: (85×0.25 + 70×0.25 + 75×0.20 + 70×0.30) = 75.2
                │
                ▼
6. Returns TechnicalScore object
   {composite_score: 75.2, reasons: [...]}
                │
                ▼
7. TechnicalAnalysisEngine.generate_signal(indicators, score, 182.50)
                │
                ├──> Score 75.2 → BUY (MEDIUM confidence)
                ├──> Entry: $182.50
                ├──> Target: $182.50 + (2.5 × $3.20) = $191.00
                ├──> Stop: $182.50 - (1.0 × $3.20) = $179.00
                └──> R/R: ($191.00-$182.50) / ($182.50-$179.00) = 2.4
                │
                ▼
8. Returns TradingSignal object
   {signal: BUY, confidence: MEDIUM, entry: 182.50, ...}
                │
                ▼
9. Create StockData object with all results
                │
                ▼
10. Export to JSON + Log to console/file
```

## File Dependencies

```
technical_analysis.py
    ├── imports: pandas, numpy, loguru
    ├── uses: config.py (get_config)
    ├── uses: models.py (TechnicalIndicators, TechnicalScore, TradingSignal)
    └── exports: TechnicalAnalysisEngine

data_fetcher.py
    ├── imports: pandas, yfinance, datetime
    ├── uses: config.py (get_config)
    └── exports: DataFetcher

models.py
    ├── imports: dataclasses, datetime, typing, enum
    └── exports: StockData, TechnicalIndicators, TechnicalScore, TradingSignal

config.py
    ├── imports: pydantic, dotenv, os
    └── exports: get_config(), AppConfig

__init__.py
    └── exports: All main classes and functions

examples/technical_analysis_example.py
    ├── imports: All from src/
    └── provides: Complete usage examples

tests/test_technical_analysis.py
    ├── imports: pytest, All from src/
    └── provides: 25+ unit tests
```

## Scalability & Performance

```
Single Stock Analysis
├── Data Fetch: ~0.5s
├── Indicator Calculation: ~0.3s
├── Scoring: ~0.1s
└── Total: ~1s per stock

Multi-Stock Analysis (Sequential)
├── 10 stocks: ~10s
├── 50 stocks: ~50s
└── 100 stocks: ~100s

Multi-Stock Analysis (Parallel - Future)
├── 10 stocks: ~2s (with 5 workers)
├── 50 stocks: ~10s (with 5 workers)
└── 100 stocks: ~20s (with 5 workers)

Optimizations Applied:
✓ Rate limiting to avoid bans
✓ Data validation before processing
✓ Efficient pandas operations
✓ Minimal API calls
✓ Error handling to skip bad data

Future Optimizations:
○ Database caching (SQLite/PostgreSQL)
○ Parallel processing (multiprocessing)
○ Batch API requests
○ Incremental updates (only new data)
○ Redis for session cache
```

---

**This architecture is designed for:**
- ✅ Modularity (easy to extend)
- ✅ Testability (comprehensive tests)
- ✅ Configurability (all parameters adjustable)
- ✅ Scalability (can handle 100+ stocks)
- ✅ Maintainability (clean code, docs)
- ✅ Production-ready (error handling, logging)

