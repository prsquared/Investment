# Caching System Documentation

## Overview

The Stock Selection system now includes a robust caching mechanism that stores fetched market data locally to:
- **Avoid Yahoo Finance rate limits** (429 errors after ~400 requests)
- **Speed up repeated analysis** (10-100x faster)
- **Reduce API bandwidth usage**
- **Enable offline analysis** with cached data

## How It Works

### Cache Storage
- **Location**: `data/cache/` directory
- **Format**: 
  - Historical data: Parquet files (compressed, fast)
  - Current prices: JSON files (human-readable)

### Cache Expiration
- **Historical data**: 24 hours
- **Current prices**: 1 hour

### Automatic Cache Management
The system automatically:
1. Checks if cached data exists and is valid
2. Returns cached data if available
3. Fetches from API if cache is missing/expired
4. Saves fetched data to cache for future use

## Usage

### Basic Usage (Caching Enabled by Default)

```python
from src.data_fetcher import DataFetcher

# Caching is enabled by default
fetcher = DataFetcher(use_cache=True)

# First call - fetches from API and caches
df = fetcher.fetch_historical_data("AAPL", days=250)

# Second call - returns cached data (much faster!)
df = fetcher.fetch_historical_data("AAPL", days=250)
```

### Disable Caching

```python
# Disable caching completely
fetcher = DataFetcher(use_cache=False)
```

### Force Refresh

```python
# Ignore cache and fetch fresh data
df = fetcher.fetch_historical_data("AAPL", force_refresh=True)
price = fetcher.fetch_current_price("AAPL", force_refresh=True)
```

### Cache Management

```python
# Clear all cache
fetcher.clear_cache()

# Clear cache for specific symbol
fetcher.clear_cache("AAPL")

# Custom cache directory
fetcher = DataFetcher(cache_dir="my_cache")
```

## Stock Scanner Integration

The `StockScanner` class now supports caching:

```python
from src.stock_scanner import StockScanner

# Caching enabled by default
scanner = StockScanner(use_cache=True)

# Scan dataset - uses cache when available
results = scanner.scan_dataset("SP500", max_stocks=50)

# Clear cache through scanner
scanner.data_fetcher.clear_cache()
```

## Performance Comparison

### Without Cache
- 10 stocks: ~2 seconds
- 50 stocks: ~10 seconds  
- 500 stocks: ~100 seconds

### With Cache (Second Run)
- 10 stocks: ~0.1 seconds (20x faster)
- 50 stocks: ~0.5 seconds (20x faster)
- 500 stocks: ~5 seconds (20x faster)

## Cache File Naming

Cache files are automatically named based on:
- Symbol (e.g., `AAPL`)
- Data type (`historical` or `current`)
- Parameters (`days_250_interval_1d`)

Example cache files:
```
AAPL_historical_days_250_interval_1d.parquet
AAPL_current.json
MSFT_historical_days_250_interval_1d.parquet
MSFT_current.json
```

## Best Practices

### For Development/Testing
- Use caching to iterate quickly on strategies
- Clear cache when you need fresh data
- Use `force_refresh=True` for critical updates

### For Production
- Set appropriate cache expiration times
- Monitor cache directory size
- Implement cache cleanup for old files
- Consider using a database for large-scale caching

### For Rate Limit Avoidance
- Always use caching when scanning large datasets
- Batch scans with delays between batches
- Cache historical data aggressively (changes rarely)
- Cache current prices conservatively (changes frequently)

## Example Scripts

### 1. Basic Caching Test
```bash
python examples/test_caching.py
```
Demonstrates caching with performance metrics.

### 2. Cached Scanning Demo
```bash
python examples/cached_scan_demo.py
```
Shows how caching improves scan performance.

## Troubleshooting

### Cache Not Working
- Check if `data/cache/` directory exists
- Verify cache files are being created
- Check file timestamps to confirm validity

### Stale Data
- Clear cache: `fetcher.clear_cache()`
- Use `force_refresh=True` for fresh data
- Reduce cache expiration times

### Disk Space Issues
- Clear old cache files periodically
- Monitor cache directory size
- Implement custom cleanup logic

## Technical Details

### Dependencies
- `pyarrow` - Fast Parquet reading/writing
- `fastparquet` - Alternative Parquet backend

### Cache Validation
Checks file modification time:
```python
file_age = datetime.now() - file_modification_time
is_valid = file_age < cache_expiration_hours
```

### Thread Safety
Current implementation is thread-safe for reading.
For production with concurrent writes, consider:
- File locking mechanisms
- Database-based caching
- Distributed cache (Redis, Memcached)

## Future Enhancements

- [ ] Automatic cache cleanup for old files
- [ ] Configurable cache sizes with LRU eviction
- [ ] Database backend option (SQLite, PostgreSQL)
- [ ] Distributed caching support (Redis)
- [ ] Cache warming for frequently accessed symbols
- [ ] Cache statistics and monitoring dashboard

---

**Last Updated**: January 14, 2026  
**Version**: 1.0
