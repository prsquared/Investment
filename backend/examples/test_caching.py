"""
Test script to demonstrate caching functionality.
"""
import sys
from pathlib import Path
from loguru import logger
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_fetcher import DataFetcher


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def test_caching():
    """Test caching functionality."""
    
    print("\n" + "="*80)
    print("CACHE FUNCTIONALITY TEST")
    print("="*80)
    
    # Test 1: First fetch (no cache)
    print("\n1. First fetch (should hit API):")
    print("-" * 80)
    fetcher = DataFetcher(use_cache=True)
    
    start = time.time()
    df1 = fetcher.fetch_historical_data("AAPL", days=250)
    price1 = fetcher.fetch_current_price("AAPL")
    time1 = time.time() - start
    
    print(f"   Time taken: {time1:.2f} seconds")
    print(f"   Records: {len(df1) if df1 is not None else 0}")
    print(f"   Price: ${price1['current_price']:.2f}" if price1 else "   Price: N/A")
    
    # Test 2: Second fetch (should use cache)
    print("\n2. Second fetch (should use cache):")
    print("-" * 80)
    
    start = time.time()
    df2 = fetcher.fetch_historical_data("AAPL", days=250)
    price2 = fetcher.fetch_current_price("AAPL")
    time2 = time.time() - start
    
    print(f"   Time taken: {time2:.2f} seconds")
    print(f"   Records: {len(df2) if df2 is not None else 0}")
    print(f"   Price: ${price2['current_price']:.2f}" if price2 else "   Price: N/A")
    print(f"   Speedup: {time1/time2:.1f}x faster!")
    
    # Test 3: Force refresh
    print("\n3. Force refresh (ignore cache):")
    print("-" * 80)
    
    start = time.time()
    df3 = fetcher.fetch_historical_data("AAPL", days=250, force_refresh=True)
    price3 = fetcher.fetch_current_price("AAPL", force_refresh=True)
    time3 = time.time() - start
    
    print(f"   Time taken: {time3:.2f} seconds")
    print(f"   Records: {len(df3) if df3 is not None else 0}")
    print(f"   Price: ${price3['current_price']:.2f}" if price3 else "   Price: N/A")
    
    # Test 4: Multiple stocks with cache
    print("\n4. Multiple stocks test:")
    print("-" * 80)
    
    symbols = ["MSFT", "GOOGL", "TSLA"]
    
    print("   First run (no cache):")
    start = time.time()
    for symbol in symbols:
        df = fetcher.fetch_historical_data(symbol, days=250)
        price = fetcher.fetch_current_price(symbol)
        if df is not None and price:
            print(f"   - {symbol}: {len(df)} records, ${price['current_price']:.2f}")
    time_first = time.time() - start
    print(f"   Time: {time_first:.2f}s")
    
    print("\n   Second run (with cache):")
    start = time.time()
    for symbol in symbols:
        df = fetcher.fetch_historical_data(symbol, days=250)
        price = fetcher.fetch_current_price(symbol)
        if df is not None and price:
            print(f"   - {symbol}: {len(df)} records, ${price['current_price']:.2f}")
    time_cached = time.time() - start
    print(f"   Time: {time_cached:.2f}s")
    print(f"   Speedup: {time_first/time_cached:.1f}x faster!")
    
    # Test 5: Cache management
    print("\n5. Cache management:")
    print("-" * 80)
    
    # Count cache files
    cache_files = list(Path("data/cache").glob("*.parquet")) + list(Path("data/cache").glob("*.json"))
    print(f"   Total cache files: {len(cache_files)}")
    
    # Clear specific symbol
    fetcher.clear_cache("AAPL")
    
    # Clear all cache
    print("   Clearing all cache...")
    fetcher.clear_cache()
    
    cache_files_after = list(Path("data/cache").glob("*.parquet")) + list(Path("data/cache").glob("*.json"))
    print(f"   Cache files after clear: {len(cache_files_after)}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nSummary:")
    print(f"  - Historical data: Cached for 24 hours")
    print(f"  - Current prices: Cached for 1 hour")
    print(f"  - Cache storage: data/cache/ directory")
    print(f"  - Cache format: Parquet (historical) + JSON (prices)")
    print(f"  - Typical speedup: 10-50x faster for cached data")
    print("\nBenefits:")
    print("  ✓ Avoid Yahoo Finance rate limits")
    print("  ✓ Faster repeated analysis")
    print("  ✓ Reduced API bandwidth")
    print("  ✓ Can work offline with cached data")
    print("="*80)


if __name__ == "__main__":
    setup_logging()
    test_caching()
