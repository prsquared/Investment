"""
Example: Dataset Collection and Scanning
Demonstrates how to collect S&P 500 and NASDAQ 100 data and scan with technical analysis.
"""
import sys
from pathlib import Path
from loguru import logger
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from dataset_collector import DatasetCollector
from stock_scanner import StockScanner


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/dataset_scanning.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def example_1_collect_datasets():
    """Example 1: Collect S&P 500 and NASDAQ 100 datasets."""
    logger.info("="*80)
    logger.info("EXAMPLE 1: Collecting Stock Datasets")
    logger.info("="*80)
    
    collector = DatasetCollector()
    
    # Fetch all datasets
    logger.info("\nFetching datasets from Wikipedia...")
    datasets = collector.fetch_all_datasets()
    
    # Display summary
    logger.info("\n" + "="*80)
    logger.info("DATASET SUMMARY")
    logger.info("="*80)
    
    summary = collector.get_dataset_summary()
    
    for dataset_name, stats in summary.items():
        logger.info(f"\n{dataset_name}:")
        logger.info(f"  Total Companies: {stats['total_companies']}")
        logger.info(f"  Unique Sectors: {stats['sectors']}")
        
        if stats['sector_breakdown']:
            logger.info("  Top 5 Sectors:")
            for sector, count in list(stats['sector_breakdown'].items())[:5]:
                logger.info(f"    - {sector}: {count} companies")
    
    logger.info("\n" + "="*80)
    logger.success("Datasets collected and saved to data/ directory")
    
    return datasets


def example_2_quick_scan():
    """Example 2: Quick scan of top 20 stocks from S&P 500."""
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 2: Quick Scan (20 Stocks from S&P 500)")
    logger.info("="*80)
    
    scanner = StockScanner()
    
    # Scan first 20 stocks
    logger.info("\nScanning stocks (this may take 1-2 minutes)...")
    results = scanner.scan_dataset(
        dataset_name="SP500",
        max_stocks=20,
        parallel=True,
        max_workers=5
    )
    
    if results.empty:
        logger.warning("No results from scan")
        return
    
    # Save results
    scanner.save_scan_results(results, "quick_scan_results.csv")
    
    # Display top picks
    logger.info("\n" + "="*80)
    logger.info("TOP 10 STOCKS BY TECHNICAL SCORE")
    logger.info("="*80)
    logger.info(f"{'Rank':<6}{'Symbol':<8}{'Score':<8}{'Signal':<8}{'Confidence':<12}{'Price':<10}")
    logger.info("-"*80)
    
    for i, row in enumerate(results.head(10).itertuples(), 1):
        logger.info(
            f"{i:<6}{row.symbol:<8}{row.technical_score:<8.1f}"
            f"{row.signal:<8}{row.confidence:<12}${row.price:<10.2f}"
        )
    
    # BUY signals
    buy_signals = results[results['signal'] == 'BUY']
    if not buy_signals.empty:
        logger.info("\n" + "="*80)
        logger.info(f"BUY SIGNALS ({len(buy_signals)} found)")
        logger.info("="*80)
        
        for row in buy_signals.head(5).itertuples():
            logger.info(f"\n{row.symbol} - ${row.price:.2f}")
            logger.info(f"  Score: {row.technical_score:.1f}/100 | Confidence: {row.confidence}")
            logger.info(f"  Entry: ${row.entry_price:.2f} | Target: ${row.target_price:.2f} | Stop: ${row.stop_loss:.2f}")
            logger.info(f"  Risk/Reward: 1:{row.risk_reward_ratio:.2f}")
            if row.reasons:
                logger.info(f"  Top Reason: {row.reasons[0]}")
    
    logger.info("\n" + "="*80)


def example_3_sector_scan():
    """Example 3: Scan technology sector stocks."""
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 3: Technology Sector Scan")
    logger.info("="*80)
    
    scanner = StockScanner()
    
    # Scan technology sector
    logger.info("\nScanning Technology sector stocks...")
    results = scanner.scan_dataset(
        dataset_name="COMBINED",
        sector_filter="Technology",
        max_stocks=30,
        parallel=True,
        max_workers=5
    )
    
    if results.empty:
        logger.warning("No technology sector results")
        return
    
    # Filter for BUY signals with good scores
    buy_signals = results[
        (results['signal'] == 'BUY') & 
        (results['technical_score'] >= 60)
    ]
    
    logger.info("\n" + "="*80)
    logger.info(f"TECHNOLOGY BUY SIGNALS (Score >= 60)")
    logger.info("="*80)
    
    if not buy_signals.empty:
        logger.info(f"Found {len(buy_signals)} strong buy signals\n")
        logger.info(f"{'Symbol':<8}{'Score':<8}{'Confidence':<12}{'Price':<10}{'Target':<10}{'R:R':<8}")
        logger.info("-"*80)
        
        for row in buy_signals.itertuples():
            logger.info(
                f"{row.symbol:<8}{row.technical_score:<8.1f}"
                f"{row.confidence:<12}${row.price:<9.2f}${row.target_price:<9.2f}1:{row.risk_reward_ratio:<7.2f}"
            )
        
        # Save tech sector results
        scanner.save_scan_results(buy_signals, "tech_sector_buy_signals.csv")
        logger.success(f"\nSaved {len(buy_signals)} tech buy signals to output/tech_sector_buy_signals.csv")
    else:
        logger.info("No strong buy signals found in technology sector")
    
    logger.info("\n" + "="*80)


def example_4_full_scan():
    """Example 4: Full scan with report generation."""
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 4: Full Dataset Scan with Report")
    logger.info("="*80)
    logger.warning("This will scan all stocks and may take 10-15 minutes...")
    logger.info("Press Ctrl+C to skip this example\n")
    
    try:
        time.sleep(3)  # Give user time to cancel
        
        scanner = StockScanner()
        
        # Full scan of combined dataset (limited for demo)
        logger.info("Starting scan of 50 stocks from combined dataset...")
        results = scanner.scan_dataset(
            dataset_name="COMBINED",
            max_stocks=50,  # Limit for demo; remove for full scan
            parallel=True,
            max_workers=8
        )
        
        if results.empty:
            logger.warning("No results from full scan")
            return
        
        # Save all results
        scanner.save_scan_results(results, "full_scan_results.csv")
        scanner.save_scan_results(results, "full_scan_results.json")
        
        # Generate and display report
        report = scanner.generate_scan_report(results, "COMBINED")
        print("\n" + report)
        
        # Save report
        with open("output/scan_report.txt", "w") as f:
            f.write(report)
        
        logger.success("\nFull scan complete! Results saved to output/ directory")
        
    except KeyboardInterrupt:
        logger.info("\nFull scan cancelled by user")


def example_5_top_picks():
    """Example 5: Get top swing trading picks."""
    logger.info("\n" + "="*80)
    logger.info("EXAMPLE 5: Top Swing Trading Picks")
    logger.info("="*80)
    
    scanner = StockScanner()
    
    # Get top BUY picks
    logger.info("\nFinding top 10 swing trading opportunities...")
    top_picks = scanner.get_top_picks(
        dataset_name="COMBINED",
        top_n=10,
        signal_type="BUY",
        min_confidence="MEDIUM"
    )
    
    if top_picks.empty:
        logger.warning("No top picks found")
        return
    
    logger.info("\n" + "="*80)
    logger.info("TOP 10 SWING TRADING PICKS")
    logger.info("="*80)
    logger.info(f"Criteria: BUY signals with MEDIUM+ confidence")
    logger.info(f"Sorted by: Technical Score (highest first)\n")
    logger.info("-"*80)
    
    for i, row in enumerate(top_picks.itertuples(), 1):
        logger.info(f"\n#{i} - {row.symbol}")
        logger.info(f"  Price: ${row.price:.2f}")
        logger.info(f"  Technical Score: {row.technical_score:.1f}/100")
        logger.info(f"    └─ Trend: {row.trend_score:.0f} | Momentum: {row.momentum_score:.0f} | Volatility: {row.volatility_score:.0f} | Volume: {row.volume_score:.0f}")
        logger.info(f"  Signal: {row.signal} ({row.confidence} confidence)")
        logger.info(f"  Trading Plan:")
        logger.info(f"    Entry: ${row.entry_price:.2f}")
        logger.info(f"    Target: ${row.target_price:.2f} (+{((row.target_price/row.entry_price)-1)*100:.1f}%)")
        logger.info(f"    Stop Loss: ${row.stop_loss:.2f} ({((row.stop_loss/row.entry_price)-1)*100:.1f}%)")
        logger.info(f"    Risk/Reward: 1:{row.risk_reward_ratio:.2f}")
        
        if row.reasons and len(row.reasons) > 0:
            logger.info(f"  Key Reasons:")
            for reason in row.reasons[:3]:
                logger.info(f"    • {reason}")
    
    # Save top picks
    scanner.save_scan_results(top_picks, "top_swing_trading_picks.csv")
    logger.success(f"\nSaved top {len(top_picks)} picks to output/top_swing_trading_picks.csv")
    
    logger.info("\n" + "="*80)


def main():
    """Run all examples."""
    setup_logging()
    
    logger.info("="*80)
    logger.info("DATASET COLLECTION & SCANNING EXAMPLES")
    logger.info("Stock Selection System - Technical Analysis")
    logger.info("="*80)
    
    try:
        # Example 1: Collect datasets
        example_1_collect_datasets()
        
        time.sleep(2)
        
        # Example 2: Quick scan
        example_2_quick_scan()
        
        time.sleep(2)
        
        # Example 3: Sector scan
        example_3_sector_scan()
        
        time.sleep(2)
        
        # Example 5: Top picks (skip example 4 for speed)
        example_5_top_picks()
        
        logger.info("\n" + "="*80)
        logger.success("ALL EXAMPLES COMPLETED!")
        logger.info("="*80)
        logger.info("\nCheck the following directories:")
        logger.info("  - data/ : Dataset CSV files (S&P 500, NASDAQ 100)")
        logger.info("  - output/ : Scan results and reports")
        logger.info("  - logs/ : Detailed execution logs")
        logger.info("\nNext steps:")
        logger.info("  1. Review the scan results in output/")
        logger.info("  2. Customize scanner parameters for your needs")
        logger.info("  3. Add fundamental analysis (coming in Part 3)")
        logger.info("  4. Build automated daily scans")
        logger.info("="*80)
        
    except KeyboardInterrupt:
        logger.warning("\n\nExecution interrupted by user")
    except Exception as e:
        logger.error(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
