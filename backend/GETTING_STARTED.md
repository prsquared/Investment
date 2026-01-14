# 🚀 Getting Started - Technical Analysis Backend

Welcome to the Stock Selection Technical Analysis module! This guide will help you get up and running quickly.

## ⚡ 5-Minute Quick Start

### Step 1: Clone and Setup (2 minutes)

```powershell
# Navigate to project
cd C:\workspace\StockSelection\Investment\backend

# Run automated setup
.\setup.ps1
```

This will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Set up configuration files
- ✅ Run tests

### Step 2: Run Your First Analysis (1 minute)

```powershell
# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Run the example
python examples\technical_analysis_example.py
```

### Step 3: View Results (1 minute)

Check the `output/` directory:
- `aapl_analysis.json` - Detailed single stock analysis
- `multi_stock_analysis.json` - Comparison of multiple stocks

### Step 4: Review Console Output (1 minute)

You should see:
```
Technical Score: 75.2/100
Signal: BUY (MEDIUM)
Entry: $182.50
Target: $191.00
Stop Loss: $179.00
Risk/Reward: 1:2.4
```

🎉 **Congratulations!** You've completed your first technical analysis!

---

## 📖 Detailed Setup Guide

### Prerequisites

**Required:**
- Windows 10/11
- Python 3.10 or higher
- PowerShell
- Internet connection (for fetching stock data)

**Optional:**
- Git (for version control)
- Visual Studio Code or JetBrains IDE
- API keys for premium data sources

### Manual Installation

If the setup script doesn't work, follow these steps:

#### 1. Install Python Dependencies

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install packages
pip install -r requirements.txt
```

#### 2. Create Directory Structure

```powershell
mkdir logs
mkdir output
mkdir data\cache
mkdir data\historical
```

#### 3. Configure Environment

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env with your text editor (optional)
notepad .env
```

#### 4. Verify Installation

```powershell
# Run tests
pytest tests\ -v

# If tests pass, you're ready!
```

---

## 🎯 Your First Custom Analysis

### Example 1: Analyze Your Favorite Stock

Create a new file `my_analysis.py`:

```python
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalysisEngine

# Initialize
fetcher = DataFetcher()
analyzer = TechnicalAnalysisEngine()

# Choose your stock
symbol = "TSLA"  # Change to any stock you want

# Fetch data
print(f"Analyzing {symbol}...")
historical_df = fetcher.fetch_historical_data(symbol, days=250)
current_data = fetcher.fetch_current_price(symbol)

if historical_df is not None and current_data:
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
    
    # Display results
    print(f"\n{'='*50}")
    print(f"Stock: {symbol}")
    print(f"Price: ${current_data['current_price']:.2f}")
    print(f"Technical Score: {score.composite_score:.1f}/100")
    print(f"Signal: {signal.signal_type.value} ({signal.confidence.value})")
    
    if signal.target_price:
        print(f"Entry: ${signal.entry_price:.2f}")
        print(f"Target: ${signal.target_price:.2f}")
        print(f"Stop Loss: ${signal.stop_loss:.2f}")
    
    print(f"\nTop Reasons:")
    for i, reason in enumerate(signal.reasons[:3], 1):
        print(f"  {i}. {reason}")
    print(f"{'='*50}")
else:
    print(f"Could not fetch data for {symbol}")
```

Run it:
```powershell
python my_analysis.py
```

### Example 2: Build a Custom Watchlist Scanner

Create `scan_watchlist.py`:

```python
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalysisEngine
from src.models import StockData
import json

# Your watchlist
watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]

# Initialize
fetcher = DataFetcher()
analyzer = TechnicalAnalysisEngine()

results = []

for symbol in watchlist:
    print(f"Scanning {symbol}...")
    
    try:
        # Fetch data
        historical_df = fetcher.fetch_historical_data(symbol, days=250)
        current_data = fetcher.fetch_current_price(symbol)
        
        if historical_df is not None and current_data:
            # Analyze
            indicators = analyzer.calculate_indicators(historical_df)
            score = analyzer.calculate_technical_score(
                indicators, 
                current_data['current_price']
            )
            signal = analyzer.generate_signal(indicators, score, current_data['current_price'])
            
            # Store result
            results.append({
                'symbol': symbol,
                'price': current_data['current_price'],
                'score': score.composite_score,
                'signal': signal.signal_type.value,
                'confidence': signal.confidence.value
            })
    except Exception as e:
        print(f"Error with {symbol}: {e}")

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

# Display
print("\n" + "="*70)
print("WATCHLIST RANKINGS")
print("="*70)
print(f"{'Rank':<6}{'Symbol':<8}{'Score':<8}{'Signal':<8}{'Confidence':<12}{'Price':<10}")
print("-"*70)

for i, result in enumerate(results, 1):
    print(f"{i:<6}{result['symbol']:<8}{result['score']:<8.1f}"
          f"{result['signal']:<8}{result['confidence']:<12}${result['price']:<10.2f}")

print("="*70)

# Save to file
with open('output/watchlist_scan.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nResults saved to: output/watchlist_scan.json")
```

Run it:
```powershell
python scan_watchlist.py
```

---

## 🔧 Configuration Guide

### Adjusting Technical Parameters

Edit `src/config.py` or create a custom config:

```python
from src.config import get_config

config = get_config()

# View current settings
print(f"RSI Period: {config.technical_analysis.rsi_period}")
print(f"RSI Overbought: {config.technical_analysis.rsi_overbought}")

# To modify, edit src/config.py directly or:
# Create a custom configuration file
```

### Common Adjustments

**For More Aggressive Signals:**
```python
# In src/config.py, adjust:
rsi_overbought = 75.0  # More lenient (was 70.0)
rsi_oversold = 25.0    # More lenient (was 30.0)

# Scoring weights (more emphasis on momentum)
weight_trend = 20.0
weight_momentum = 35.0
weight_volatility = 15.0
weight_volume = 30.0
```

**For More Conservative Signals:**
```python
# In src/config.py, adjust:
min_volume = 1_000_000      # Higher volume requirement
min_price = 10.0            # Avoid lower-priced stocks

# Require stronger scores for BUY signals
# In technical_analysis.py, adjust signal thresholds
```

---

## 📊 Understanding the Output

### Technical Score Breakdown

```json
{
  "trend_score": 85.0,      // 0-100: MA alignment, crossovers
  "momentum_score": 70.0,   // 0-100: RSI, MACD signals
  "volatility_score": 75.0, // 0-100: BB position, ATR
  "volume_score": 70.0,     // 0-100: Volume ratio
  "composite_score": 75.2   // Weighted average
}
```

**Interpretation:**
- **80-100**: Strongly bullish - High probability setup
- **60-79**: Bullish - Good setup
- **40-59**: Neutral - Wait for clearer signal
- **20-39**: Bearish - Avoid or consider selling
- **0-19**: Strongly bearish - Strong sell signal

### Trading Signal Fields

```json
{
  "signal": "BUY",           // BUY, SELL, or HOLD
  "confidence": "MEDIUM",    // HIGH, MEDIUM, or LOW
  "entry_price": 182.50,     // Current price
  "target_price": 191.00,    // Profit target (2-3x ATR)
  "stop_loss": 179.00,       // Risk management (1-1.5x ATR)
  "reasons": [...]           // Detailed explanation
}
```

**How to Use:**
1. Only take BUY signals with MEDIUM or HIGH confidence
2. Always use the stop loss
3. Consider taking partial profits at target
4. Review reasons to understand the setup

---

## 🧪 Testing Your Changes

### Run All Tests

```powershell
pytest tests\ -v
```

### Run Specific Test

```powershell
pytest tests\test_technical_analysis.py::TestTechnicalAnalysisEngine::test_calculate_rsi -v
```

### Run with Coverage

```powershell
pytest tests\ --cov=src --cov-report=html
# View coverage: htmlcov\index.html
```

### Write Your Own Test

```python
# tests/test_my_feature.py
import pytest
from src.technical_analysis import TechnicalAnalysisEngine

def test_my_custom_indicator():
    engine = TechnicalAnalysisEngine()
    # Your test code here
    assert True
```

---

## 🐛 Troubleshooting

### Issue: "Module not found"

**Solution:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "No data returned for symbol"

**Possible causes:**
1. Invalid symbol (check spelling)
2. Stock delisted or trading halted
3. Internet connection issues
4. Rate limiting by API

**Solution:**
```python
# Add error handling
try:
    df = fetcher.fetch_historical_data("AAPL")
    if df is None:
        print("No data available")
except Exception as e:
    print(f"Error: {e}")
```

### Issue: "Insufficient historical data"

**Solution:**
```python
# Check data length before analysis
if len(df) < 200:
    print(f"Only {len(df)} days of data (need 200+)")
else:
    indicators = analyzer.calculate_indicators(df)
```

### Issue: Tests failing

**Common causes:**
1. Missing dependencies
2. Network issues (can't fetch test data)
3. API changes

**Solution:**
```powershell
# Update dependencies
pip install --upgrade -r requirements.txt

# Run tests with verbose output
pytest tests\ -v -s
```

### Issue: Rate limiting errors

**Solution:**
```python
# Increase delay in config.py
api_call_delay = 1.0  # Increased from 0.2

# Or add manual delay in your script
import time
time.sleep(1)  # Wait 1 second between requests
```

---

## 📚 Next Steps

### 1. Learn the Indicators

Read `QUICK_REFERENCE.md` to understand:
- How each indicator works
- What signals to look for
- Trading patterns and setups

### 2. Backtest a Strategy

Create historical analysis:
```python
# Analyze past performance
for date in historical_dates:
    # Run analysis as of that date
    # Track if signals were profitable
```

### 3. Build a Dashboard

Ideas:
- Web interface with Flask/FastAPI
- Real-time updates with WebSockets
- Chart visualization with Plotly
- Alert system (email, SMS)

### 4. Add More Features

Extend the system:
- Additional technical indicators
- Chart pattern recognition
- Support/resistance levels
- Candlestick patterns
- Sector analysis

### 5. Integrate Fundamental Analysis

Combine with Part 3:
- P/E ratios, earnings growth
- Financial health metrics
- Combined technical + fundamental score

---

## 💡 Tips for Success

### Trading Tips

1. **Always use stop losses** - Protect your capital
2. **Don't chase** - Wait for pullbacks in uptrends
3. **Confirm with volume** - Low volume = weak signal
4. **Be patient** - Wait for high-confidence setups
5. **Take partial profits** - Secure gains, let winners run

### Development Tips

1. **Test with real data** - Use actual stock symbols
2. **Log everything** - Debug with detailed logs
3. **Handle errors** - Markets are unpredictable
4. **Document changes** - Comment your code
5. **Version control** - Use Git for tracking

### Performance Tips

1. **Cache data** - Don't refetch unnecessarily
2. **Batch requests** - Analyze multiple stocks efficiently
3. **Use async** - For parallel processing (future)
4. **Database** - Store historical data locally
5. **Monitor usage** - Track API rate limits

---

## 🤝 Getting Help

### Resources

1. **Documentation**
   - `README.md` - Full user guide
   - `QUICK_REFERENCE.md` - Trading guide
   - `ARCHITECTURE.md` - System design
   - Code comments and docstrings

2. **Example Code**
   - `examples/technical_analysis_example.py`
   - This file (GETTING_STARTED.md)

3. **Tests**
   - `tests/test_technical_analysis.py`
   - Show how to use each function

### Common Questions

**Q: Which indicators are most important?**
A: For swing trading, focus on trend (MAs), momentum (RSI), and volume. ATR is critical for stop-loss placement.

**Q: What's a good technical score for buying?**
A: 70+ is strong, 60-70 is good. Below 55, wait for better setup.

**Q: How many stocks should I analyze?**
A: Start with 5-10 stocks you know well. Expand as you gain confidence.

**Q: Can I use this for day trading?**
A: This is optimized for swing trading (2-30 days). For day trading, use shorter timeframes and different indicators.

**Q: Is this financial advice?**
A: No! This is educational software. Always do your own research and consider consulting a financial advisor.

---

## ✅ Checklist for Your First Week

**Day 1: Setup**
- [ ] Install Python and dependencies
- [ ] Run setup script successfully
- [ ] Execute example script
- [ ] Review output files

**Day 2-3: Learning**
- [ ] Read QUICK_REFERENCE.md
- [ ] Understand each indicator
- [ ] Analyze 5-10 different stocks
- [ ] Review scoring methodology

**Day 4-5: Customization**
- [ ] Create custom watchlist
- [ ] Modify configuration parameters
- [ ] Write custom analysis script
- [ ] Test with different timeframes

**Day 6-7: Advanced**
- [ ] Write unit tests for custom code
- [ ] Implement error handling
- [ ] Create backtesting framework
- [ ] Plan next features

---

## 🎓 Learning Resources

### Technical Analysis
- "Technical Analysis of the Financial Markets" by John Murphy
- Investopedia.com - Technical indicators
- TradingView.com - Chart analysis practice

### Python & Data Science
- Pandas documentation
- NumPy tutorials
- Python for Finance courses

### Trading Strategy
- "Swing Trading for Dummies"
- YouTube: Technical analysis channels
- Paper trading platforms (practice without risk)

---

## 🚀 You're Ready!

You now have everything you need to start analyzing stocks with technical analysis. Remember:

✅ Start small and learn gradually
✅ Test thoroughly before real trading
✅ Always manage risk with stop losses
✅ Keep learning and improving

**Happy Trading! 📈**

---

*Questions? Check the documentation or review the example code!*

