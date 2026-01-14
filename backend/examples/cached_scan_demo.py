"""
Quick demo: Cached scanning for fast re-analysis.
"""
import sys
from pathlib import Path
from loguru import logger
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from stock_scanner import StockScanner


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )


def main():
    """Demonstrate cached scanning."""
    setup_logging()
    
    print("\n" + "="*80)
    print("CACHED SCANNING DEMO")
    print("="*80)
    
    # Initialize scanner with caching enabled
    scanner = StockScanner(use_cache=True)
    
    # Select a small set of stocks to scan
    symbols_to_scan = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", 
                       "META", "AMZN", "NFLX", "AMD", "INTC"]
    
    print(f"\nScanning {len(symbols_to_scan)} stocks...")
    print("Stocks:", ", ".join(symbols_to_scan))
    
    # First scan - will fetch from API
    print("\n" + "-"*80)
    print("FIRST SCAN (fetching from API):")
    print("-"*80)
    start = time.time()
    
    results_first = scanner.scan_dataset(
        dataset_name="COMBINED",
        max_stocks=len(symbols_to_scan),
        parallel=True,
        max_workers=5
    )
    
    time_first = time.time() - start
    print(f"\n✓ First scan completed in: {time_first:.2f} seconds")
    print(f"  Analyzed {len(results_first)} stocks")
    
    if not results_first.empty:
        top = results_first.head(3)
        print(f"\n  Top 3 stocks:")
        for i, row in enumerate(top.itertuples(), 1):
            print(f"    {i}. {row.symbol}: {row.technical_score:.1f} ({row.signal})")
    
    # Second scan - will use cache
    print("\n" + "-"*80)
    print("SECOND SCAN (using cache):")
    print("-"*80)
    start = time.time()
    
    results_second = scanner.scan_dataset(
        dataset_name="COMBINED",
        max_stocks=len(symbols_to_scan),
        parallel=True,
        max_workers=5
    )
    
    time_second = time.time() - start
    print(f"\n✓ Second scan completed in: {time_second:.2f} seconds")
    print(f"  Analyzed {len(results_second)} stocks")
    
    # Calculate speedup
    if time_second > 0:
        speedup = time_first / time_second
        print(f"\n🚀 SPEEDUP: {speedup:.1f}x faster with caching!")
        print(f"  Time saved: {time_first - time_second:.2f} seconds")
    
    # Save results
    if not results_second.empty:
        output_file = scanner.save_scan_results(results_second, "cached_scan_demo.csv")
        print(f"\n  Results saved to: {output_file}")
    
    # Show cache statistics
    cache_dir = Path("data/cache")
    parquet_files = list(cache_dir.glob("*.parquet"))
    json_files = list(cache_dir.glob("*.json"))
    
    print("\n" + "="*80)
    print("CACHE STATISTICS")
    print("="*80)
    print(f"  Historical data files: {len(parquet_files)}")
    print(f"  Current price files: {len(json_files)}")
    print(f"  Total cache files: {len(parquet_files) + len(json_files)}")
    print(f"  Cache directory: {cache_dir.absolute()}")
    
    print("\n" + "="*80)
    print("BENEFITS OF CACHING")
    print("="*80)
    print("  ✓ Avoid Yahoo Finance rate limits")
    print("  ✓ 10-100x faster repeated analysis")
    print("  ✓ Work offline with cached data")
    print("  ✓ Iterate quickly on strategies")
    print("  ✓ Historical data cached for 24 hours")
    print("  ✓ Current prices cached for 1 hour")
    
    print("\n" + "="*80)
    print("CACHE MANAGEMENT")
    print("="*80)
    print("  Clear all cache:")
    print("    scanner.data_fetcher.clear_cache()")
    print("\n  Clear specific stock:")
    print("    scanner.data_fetcher.clear_cache('AAPL')")
    print("\n  Force refresh (ignore cache):")
    print("    fetcher.fetch_historical_data('AAPL', force_refresh=True)")
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
