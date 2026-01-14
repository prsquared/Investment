# How to Run the Stock Selection System

## Quick Start (5 Minutes)

### Step 1: Prerequisites

**Required:**
- Python 3.10 or higher
- Windows 10/11 with PowerShell
- Internet connection (for fetching stock data)

**Check Python version:**
```powershell
python --version
```

### Step 2: Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/prsquared/Investment.git
cd Investment\backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir logs, output, data\cache, data\historical -Force
```

### Step 3: Run Your First Analysis

```powershell
# Run the basic technical analysis example
python examples\technical_analysis_example.py
```

**Expected output:**
- Analysis of AAPL, MSFT, GOOGL, TSLA, NVDA
- Technical scores (0-100)
- BUY/SELL/HOLD signals
- Entry/Target/Stop-Loss prices
- Results saved to `output/` directory

---

## Available Scripts

### 1. Basic Technical Analysis
**File:** `examples\technical_analysis_example.py`

Analyzes individual stocks with technical indicators.

```powershell
python examples\technical_analysis_example.py
```

**Output:**
- `output\aapl_analysis.json` - Detailed single stock analysis
- `output\multi_stock_analysis.json` - Multiple stock comparison
- Console output with top picks

---

### 2. Dataset Collection & Scanning
**File:** `examples\dataset_scanning_example.py`

Fetches S&P 500 and NASDAQ 100 companies and scans them.

```powershell
python examples\dataset_scanning_example.py
```

**What it does:**
- Downloads S&P 500 companies (503 stocks)
- Downloads NASDAQ 100 companies (101 stocks)
- Quick scan of 20 stocks
- Technology sector scan
- Top 10 swing trading picks

**Output:**
- `data\sp500_companies.csv` - S&P 500 list
- `data\nasdaq100_companies.csv` - NASDAQ 100 list
- `data\combined_companies.csv` - Combined dataset (518 stocks)
- `output\quick_scan_results.csv` - Scan results
- `output\tech_sector_buy_signals.csv` - Tech sector signals
- `output\top_swing_trading_picks.csv` - Top picks

**Note:** Full scan takes 10-15 minutes due to API rate limits.

---

### 3. Cached Scanning Demo
**File:** `examples\cached_scan_demo.py`

Demonstrates caching system for faster repeated analysis.

```powershell
python examples\cached_scan_demo.py
```

**What it shows:**
- First scan: Fetches from Yahoo Finance API
- Second scan: Uses cached data (20-100x faster)
- Performance comparison
- Cache statistics

**Output:**
- `output\cached_scan_demo.csv` - Scan results
- `data\cache\*.parquet` - Cached historical data
- `data\cache\*.json` - Cached current prices

---

### 4. Caching Tests
**File:** `examples\test_caching.py`

Tests the caching functionality with performance metrics.

```powershell
python examples\test_caching.py
```

**What it tests:**
- Cache hit/miss behavior
- Force refresh functionality
- Multiple stocks caching
- Cache management
- Speedup measurements

---

## Common Workflows

### Workflow 1: Daily Stock Analysis

```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Run full analysis
python examples\dataset_scanning_example.py

# Check results
Get-Content output\top_swing_trading_picks.csv
```

### Workflow 2: Quick Stock Check

```python
# Create a custom script: my_quick_check.py
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalysisEngine

fetcher = DataFetcher(use_cache=True)
analyzer = TechnicalAnalysisEngine()

# Your watchlist
symbols = ["AAPL", "TSLA", "NVDA"]

for symbol in symbols:
    df = fetcher.fetch_historical_data(symbol, days=250)
    price = fetcher.fetch_current_price(symbol)
    
    if df is not None and price:
        indicators = analyzer.calculate_indicators(df)
        score = analyzer.calculate_technical_score(indicators, price['current_price'])
        signal = analyzer.generate_signal(indicators, score, price['current_price'])
        
        print(f"{symbol}: ${price['current_price']:.2f} | Score: {score.composite_score:.1f} | {signal.signal_type.value}")
```

Run it:
```powershell
python my_quick_check.py
```

### Workflow 3: Sector-Specific Analysis

```python
# Create: analyze_tech_sector.py
from src.stock_scanner import StockScanner

scanner = StockScanner(use_cache=True)

# Scan only technology sector
results = scanner.scan_dataset(
    dataset_name="COMBINED",
    sector_filter="Technology",
    signal_filter="BUY",
    min_score=60,
    parallel=True
)

# Display results
print(results[['symbol', 'price', 'technical_score', 'signal', 'confidence']])

# Save
scanner.save_scan_results(results, "tech_buy_signals.csv")
```

---

## Directory Structure After Running

```
Investment/
├── backend/
│   ├── data/
│   │   ├── cache/               # Cached stock data (auto-created)
│   │   │   ├── AAPL_historical_days_250_interval_1d.parquet
│   │   │   ├── AAPL_current.json
│   │   │   └── ...
│   │   ├── sp500_companies.csv  # S&P 500 list
│   │   ├── nasdaq100_companies.csv
│   │   └── combined_companies.csv
│   ├── output/                  # Analysis results (auto-created)
│   │   ├── aapl_analysis.json
│   │   ├── multi_stock_analysis.json
│   │   ├── quick_scan_results.csv
│   │   └── top_swing_trading_picks.csv
│   ├── logs/                    # Execution logs (auto-created)
│   │   └── technical_analysis.log
│   ├── examples/                # Example scripts
│   ├── src/                     # Core source code
│   └── tests/                   # Unit tests
```

---

## Viewing Results

### Console Output
Results are printed to console with:
- Stock symbol
- Current price
- Technical score (0-100)
- Signal (BUY/SELL/HOLD)
- Confidence (HIGH/MEDIUM/LOW)
- Entry/Target/Stop-Loss prices

### CSV Files
Open with Excel or any CSV viewer:
```powershell
# Open in default app
Start-Process output\top_swing_trading_picks.csv
```

### JSON Files
View with any text editor or:
```powershell
Get-Content output\aapl_analysis.json | ConvertFrom-Json | Format-List
```

---

## Troubleshooting

### Issue: "Module not found"
```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "No data returned" or Rate Limiting
**Cause:** Yahoo Finance rate limiting (429 errors)

**Solution:** Use caching!
```python
# Cache is enabled by default
fetcher = DataFetcher(use_cache=True)  # ✓ Good
scanner = StockScanner(use_cache=True)  # ✓ Good
```

### Issue: "Insufficient historical data"
**Cause:** Stock is new or has less than 200 trading days

**Solution:** Skip or use fewer days
```python
df = fetcher.fetch_historical_data(symbol, days=100)  # Reduce from 250
```

### Issue: Script runs slowly
**Solution 1:** Use caching (enabled by default)
```python
# Second run will be 20-100x faster
scanner = StockScanner(use_cache=True)
```

**Solution 2:** Reduce number of stocks
```python
results = scanner.scan_dataset(max_stocks=20)  # Instead of 500
```

**Solution 3:** Use parallel processing
```python
results = scanner.scan_dataset(parallel=True, max_workers=8)
```

---

## Performance Tips

### For Faster Scans
1. **Use caching** - 20-100x speedup on repeated runs
2. **Parallel processing** - Set `max_workers=8` for multi-core CPUs
3. **Limit scope** - Scan specific sectors or top N stocks
4. **Batch processing** - Split large scans into smaller batches

### For Better Results
1. **Fresh data** - Use `force_refresh=True` for critical decisions
2. **Filter signals** - Set `min_score=60` for higher quality signals
3. **Sector focus** - Analyze specific sectors for better context
4. **Multiple timeframes** - Run analysis with different day ranges

---

## Next Steps

### 1. Customize Parameters
Edit `src\config.py` to adjust:
- RSI thresholds (overbought/oversold)
- Moving average periods
- Scoring weights
- Minimum volume/price filters

### 2. Build Custom Strategies
Create your own analysis scripts using the core modules:
- `src\data_fetcher.py` - Fetch stock data
- `src\technical_analysis.py` - Calculate indicators
- `src\stock_scanner.py` - Scan datasets
- `src\dataset_collector.py` - Manage stock lists

### 3. Add More Features
- Fundamental analysis (P/E, EPS, Revenue)
- Chart pattern recognition
- Backtest historical performance
- Automated alerts (email/SMS)
- Web dashboard

### 4. Run Tests
```powershell
# Run all tests
pytest tests\ -v

# Run specific test
pytest tests\test_technical_analysis.py -v

# Run with coverage
pytest tests\ --cov=src --cov-report=html
```

---

## Additional Resources

- **Main Documentation**: `README.md`
- **Getting Started Guide**: `GETTING_STARTED.md`
- **Caching Documentation**: `CACHING.md`
- **Trading Reference**: `QUICK_REFERENCE.md`
- **System Architecture**: `ARCHITECTURE.md`

---

## Support & Contributing

### Questions?
- Check the documentation files in `backend/`
- Review example scripts in `examples/`
- Check logs in `logs/technical_analysis.log`

### Found a Bug?
- Check if it's a known issue
- Review troubleshooting section
- Submit issue with error details and logs

### Want to Contribute?
- Fork the repository
- Create a feature branch
- Submit pull request with description

---

**Happy Trading! 📈**

*Remember: This is for educational purposes only. Not financial advice. Always do your own research.*
