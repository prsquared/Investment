# Streamlit Dashboard

## Run the Dashboard

```powershell
# From backend directory
cd C:\workspace\StockSelection\Investment\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run Streamlit
streamlit run app.py
```

Or use Python launcher:
```powershell
C:/workspace/StockSelection/Investment/backend/.venv/Scripts/python.exe -m streamlit run app.py
```

The dashboard will open in your browser at http://localhost:8501

## Features

### 📊 Stock Scanner
- **Dataset Selection**: S&P 500, NASDAQ 100, or Combined (518 stocks)
- **Sector Filter**: Filter by specific industry sectors
- **Signal Filter**: Show only BUY, SELL, or HOLD signals
- **Score Threshold**: Set minimum technical score (0-100)
- **Max Stocks**: Limit scan size to avoid rate limits

### 📈 Interactive Charts
- **Candlestick Charts**: OHLC price data with zoom/pan
- **Technical Indicators**: 
  - Moving Averages (SMA 20, 50, 200)
  - Bollinger Bands
  - RSI (Relative Strength Index)
  - Volume bars
- **Multi-timeframe**: Adjustable chart periods

### 🎯 Results Display
- **Summary Metrics**: Total stocks, buy signals, average score
- **Sortable Table**: Sort by score, price, or any metric
- **Detailed View**: Individual stock analysis with:
  - Entry/Target/Stop-Loss prices
  - Score breakdown (Trend, Momentum, Volatility, Volume)
  - Key trading signals
- **Export**: Download results as CSV

### 💾 Cache Management
- **Smart Caching**: 24h for historical data, 1h for prices
- **Clear Cache**: Manual cache invalidation
- **Performance**: 20-100x speedup on repeated scans

## Usage Tips

### First Time Setup
1. Run the dashboard - it will auto-fetch datasets if needed
2. Start with a small scan (20-50 stocks) to test
3. Use cached data for faster subsequent scans

### Recommended Workflow
1. **Morning Scan**: Run with "All" sectors, min score 60, BUY signals
2. **Sector Deep Dive**: Filter to specific sector (e.g., Technology)
3. **Individual Analysis**: Click stocks to view charts and details
4. **Export**: Download top picks for further research

### Avoiding Rate Limits
- Keep max stocks ≤ 50 for first scan
- Use cache (enabled by default)
- Wait 5-10 minutes between large scans if hitting limits
- Results are cached, so second scan is instant

## Customization

### Adjust Cache TTL
Edit `src/data_fetcher.py`:
```python
self.historical_cache_hours = 24  # Change to 48 for 2 days
self.current_price_cache_hours = 1  # Change to 0.5 for 30 min
```

### Modify Scoring Weights
Edit `src/config.py`:
```python
technical_weights = {
    "trend": 0.35,      # Increase for trend-following
    "momentum": 0.30,   # Increase for momentum trading
    "volatility": 0.20,
    "volume": 0.15
}
```

### Add Custom Indicators
Edit `src/technical_analysis.py` to add your own indicators.

## Deployment

### Local Network Access
Allow access from other devices on your network:
```powershell
streamlit run app.py --server.address 0.0.0.0
```

### Streamlit Cloud (Free)
1. Push code to GitHub (already done!)
2. Go to https://streamlit.io/cloud
3. Connect GitHub repo
4. Deploy app.py
5. Share public URL

### Docker (Production)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Troubleshooting

### "Module not found" errors
```powershell
pip install -r requirements.txt
```

### Port already in use
```powershell
streamlit run app.py --server.port 8502
```

### Charts not displaying
Clear browser cache or try incognito mode.

### Slow performance
- Reduce max_stocks parameter
- Enable caching (default)
- Use sector filters to narrow scope

## Keyboard Shortcuts

- `Ctrl + R`: Rerun the app
- `Ctrl + Shift + R`: Clear cache and rerun
- `C`: Toggle sidebar
- `M`: Toggle menu

## Next Steps

Enhance the dashboard with:
- 📊 Add fundamental analysis metrics (P/E, EPS, etc.)
- 🔔 Email/SMS alerts for new signals
- 📅 Schedule daily scans
- 🗄️ Database backend for historical tracking
- 🔐 User authentication
- 📱 Mobile-responsive design improvements

---

**Happy Trading! 📈**

*Remember: This is for educational purposes only. Not financial advice.*
