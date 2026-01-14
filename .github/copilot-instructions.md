# GitHub Copilot Instructions for Stock Selection Project

## Project Overview
This is a stock selection system for **swing trading in the US Market** that combines:
- **Technical Analysis**: Chart patterns, indicators, momentum, volume analysis
- **Fundamental Analysis**: Financial metrics, earnings, growth rates, valuation ratios
- **Target**: Identify high-probability swing trade opportunities (typically 2-30 day holding periods)

## Context & Domain Knowledge

### Trading Strategy Focus
- **Market**: US equities (NYSE, NASDAQ)
- **Style**: Swing trading (not day trading or long-term investing)
- **Timeframe**: 2-30 days typical hold period
- **Analysis**: Multi-factor approach combining technicals and fundamentals

### Key Technical Indicators to Consider
- Moving Averages (SMA, EMA): 20, 50, 200 periods
- RSI (Relative Strength Index): Overbought/oversold levels
- MACD (Moving Average Convergence Divergence)
- Volume analysis and volume spikes
- Support and resistance levels
- Chart patterns: flags, triangles, breakouts, reversals
- Bollinger Bands
- ATR (Average True Range) for volatility

### Key Fundamental Metrics to Consider
- P/E Ratio (Price-to-Earnings)
- EPS Growth (Earnings Per Share)
- Revenue Growth
- Profit Margins
- ROE (Return on Equity)
- Debt-to-Equity Ratio
- Free Cash Flow
- Earnings surprise history
- Analyst ratings and price targets
- Institutional ownership changes

### Data Sources & APIs
When suggesting data sources, prefer:
- Alpha Vantage (free tier available)
- Yahoo Finance API (yfinance for Python)
- IEX Cloud
- Polygon.io
- Financial Modeling Prep API
- EODHD (End of Day Historical Data)
- Finnhub

## Code Generation Guidelines

### General Principles
1. **Data Quality**: Always validate and clean market data before analysis
2. **Error Handling**: Financial data can be missing/delayed - handle gracefully
3. **Performance**: Optimize for scanning hundreds/thousands of stocks
4. **Logging**: Log all trading signals, scores, and decisions for backtesting
5. **Configuration**: Use config files for thresholds, weights, and parameters
6. **Testing**: Include unit tests for calculations and integration tests for workflows

### Language-Specific Guidance

#### Python
- Use pandas for data manipulation and analysis
- Use numpy for numerical computations
- Consider libraries: yfinance, pandas-ta, ta-lib, backtrader, zipline
- Use dataclasses or pydantic for data models
- Follow PEP 8 style guidelines
- Type hints are mandatory for function signatures

#### JavaScript/TypeScript
- Use TypeScript for type safety
- Consider libraries: yahoo-finance2, technicalindicators, node-fetch
- Use async/await for API calls
- Implement rate limiting for API requests
- Use classes or interfaces for data structures

#### Java
- Use robust HTTP clients (OkHttp, Apache HttpClient)
- Consider libraries: ta4j for technical analysis
- Use BigDecimal for financial calculations (avoid floating point errors)
- Implement builder patterns for complex objects
- Use Stream API for data processing

### Naming Conventions
- **Stock symbols**: Always uppercase (e.g., "AAPL", "MSFT")
- **Price variables**: Use descriptive names like `closePrice`, `openPrice`, not just `price`
- **Indicators**: Prefix with indicator type (e.g., `rsi14`, `sma50`, `ema20`)
- **Scores**: Use clear naming like `technicalScore`, `fundamentalScore`, `compositeScore`
- **Dates**: Use ISO format (YYYY-MM-DD) or Unix timestamps

### Code Patterns

#### Stock Data Model
```python
# Example structure for stock data
class StockData:
    symbol: str
    current_price: float
    volume: int
    market_cap: float
    technical_indicators: dict
    fundamental_metrics: dict
    score: float
    signals: list[str]
```

#### Scoring System
- Technical score: 0-100 scale
- Fundamental score: 0-100 scale
- Composite score: Weighted combination (e.g., 60% technical, 40% fundamental for swing trading)
- Document scoring criteria clearly

#### Signal Generation
- Generate clear BUY/SELL/HOLD signals
- Include confidence level (e.g., HIGH, MEDIUM, LOW)
- Provide reasoning for each signal
- Include entry price, target price, stop-loss

### Data Handling Best Practices

1. **Caching**: Cache API responses to avoid rate limits
2. **Batch Processing**: Fetch data in batches when possible
3. **Historical Data**: Store historical data locally for backtesting
4. **Real-time Updates**: Clearly separate real-time vs end-of-day logic
5. **Time Zones**: Always use market time zone (ET for US markets)

### Financial Calculation Standards

1. **Precision**: Use appropriate decimal precision (2 decimals for prices, 4 for ratios)
2. **Percentages**: Clearly indicate if values are percentages or decimals
3. **Returns**: Calculate returns correctly: (current - previous) / previous * 100
4. **Avoid Division by Zero**: Always check denominators
5. **Handle Stock Splits**: Adjust historical prices for splits and dividends

### Security & API Key Management

1. **Never hardcode API keys** - use environment variables or config files
2. **Add .env to .gitignore**
3. **Use secrets management** for production
4. **Implement rate limiting** to respect API quotas
5. **Handle authentication errors** gracefully

### Testing Requirements

1. **Unit Tests**: Test all calculation functions with known inputs/outputs
2. **Integration Tests**: Test API integrations with mock data
3. **Backtesting**: Validate strategy performance on historical data
4. **Edge Cases**: Test with missing data, delisted stocks, extreme values

### Documentation Standards

1. **Function Docstrings**: Explain parameters, return values, and purpose
2. **Algorithm Comments**: Explain the "why" behind thresholds and weights
3. **README**: Include setup instructions, API key configuration, usage examples
4. **Strategy Documentation**: Document the trading logic and rationale

## Specific Feature Implementations

### When Implementing Stock Scanners
- Filter by minimum volume (e.g., >500K daily average)
- Filter by minimum price (e.g., >$5 to avoid penny stocks)
- Filter by market cap if relevant
- Implement pagination for large result sets
- Return top N candidates sorted by composite score

### When Implementing Technical Analysis
- Use at least 200 days of historical data for reliable indicators
- Handle insufficient data gracefully (new IPOs)
- Normalize indicators to comparable scales
- Consider multiple timeframes (daily, weekly)

### When Implementing Fundamental Analysis
- Use most recent quarterly/annual data
- Handle missing fundamentals (not all stocks have all metrics)
- Compare metrics to industry averages when possible
- Consider growth trends, not just absolute values

### When Implementing Backtesting
- Use realistic assumptions (slippage, commissions)
- Avoid look-ahead bias
- Test on out-of-sample data
- Calculate key metrics: Sharpe ratio, max drawdown, win rate
- Generate performance reports with charts

### When Implementing Alerts/Notifications
- Support multiple channels (email, SMS, webhook, desktop notification)
- Include all relevant information in alerts
- Implement throttling to avoid spam
- Allow user-configurable alert criteria

## Performance Optimization

1. **Parallel Processing**: Scan multiple stocks concurrently
2. **Database Indexing**: Index by symbol, date for fast queries
3. **Incremental Updates**: Only fetch new data, not full history
4. **Caching Strategy**: Cache expensive calculations
5. **Lazy Loading**: Load detailed data only for top candidates

## Error Handling Patterns

```python
# Example error handling for API calls
try:
    stock_data = fetch_stock_data(symbol)
except RateLimitError:
    # Wait and retry with exponential backoff
    pass
except DataNotFoundError:
    # Log and skip this symbol
    pass
except APIError as e:
    # Log error, continue with next symbol
    pass
```

## Configuration Management

Externalize these parameters:
- Technical indicator periods and thresholds
- Fundamental metric thresholds
- Scoring weights (technical vs fundamental)
- Risk parameters (stop-loss percentages)
- API endpoints and credentials
- Stock universe (watchlist, indices to scan)

## Comments & Code Style

- **Prefer clear code over comments** where possible
- **Comment complex algorithms** and non-obvious logic
- **Explain thresholds**: Why RSI > 70 is overbought, why P/E < 15 is value
- **Document assumptions**: Market hours, data freshness, etc.
- **Use TODO comments** for future improvements

## Example Workflow Structure

```
1. Data Collection
   ├── Fetch stock universe (S&P 500, NASDAQ 100, custom watchlist)
   ├── Fetch price data and volume
   ├── Fetch fundamental data
   └── Store in database/cache

2. Technical Analysis
   ├── Calculate indicators (RSI, MACD, Moving Averages)
   ├── Identify chart patterns
   ├── Detect support/resistance levels
   └── Generate technical score

3. Fundamental Analysis
   ├── Calculate/fetch key ratios
   ├── Analyze growth trends
   ├── Check earnings quality
   └── Generate fundamental score

4. Signal Generation
   ├── Combine technical + fundamental scores
   ├── Apply filters (volume, price, liquidity)
   ├── Rank candidates
   └── Generate actionable signals

5. Output & Alerts
   ├── Generate reports
   ├── Send notifications
   ├── Update dashboard
   └── Log for backtesting
```

## Risk Management Reminders

When generating code for position sizing or risk management:
- Always suggest stop-loss levels
- Calculate position size based on risk tolerance
- Consider portfolio diversification (max % per position)
- Account for correlation between positions
- Suggest take-profit targets based on R:R ratio

## Backtesting Considerations

- Use adjusted prices (split/dividend adjusted)
- Implement realistic order execution (next bar open, not current close)
- Account for trading costs (commission + slippage)
- Separate training and testing periods
- Walk-forward analysis for robustness
- Monte Carlo simulation for confidence intervals

## Regulatory & Compliance Notes

- This is for **personal/educational use** - not financial advice
- Include disclaimers in any user-facing output
- Do not guarantee returns or performance
- Clearly label signals as algorithmic suggestions
- Maintain audit trail of decisions

## Latest US Market Context (as of January 2026)

- Standard trading hours: 9:30 AM - 4:00 PM ET
- Pre-market: 4:00 AM - 9:30 AM ET
- After-hours: 4:00 PM - 8:00 PM ET
- Consider extended hours data if relevant
- Be aware of market holidays
- Account for earnings season volatility

## Final Reminders

1. **Financial accuracy is critical** - double-check all calculations
2. **Handle edge cases** - markets are unpredictable
3. **Think like a trader** - practical, actionable outputs
4. **Optimize for swing trading timeframe** - not day trading or investing
5. **Test thoroughly** - financial code needs extra validation
6. **Document strategy rationale** - explain the "why" behind decisions

---

When in doubt, prioritize:
1. **Correctness** over speed
2. **Clarity** over cleverness  
3. **Robustness** over features
4. **Testing** over shipping

Happy coding! 🚀📈

