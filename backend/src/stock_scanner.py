"""
Stock Scanner - Scan large datasets with technical analysis.
"""
from typing import List, Dict, Optional, Tuple
import pandas as pd
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path
import json

try:
    from .dataset_collector import DatasetCollector
    from .data_fetcher import DataFetcher
    from .technical_analysis import TechnicalAnalysisEngine
    from .fundamental_analysis import FundamentalAnalysisEngine
    from .models import StockData, TradingSignal, SignalType, ConfidenceLevel
except ImportError:
    from dataset_collector import DatasetCollector
    from data_fetcher import DataFetcher
    from technical_analysis import TechnicalAnalysisEngine
    from fundamental_analysis import FundamentalAnalysisEngine
    from models import StockData, TradingSignal, SignalType, ConfidenceLevel


class StockScanner:
    """Scan stock datasets with technical and fundamental analysis."""

    def __init__(
        self, 
        output_dir: str = "output", 
        use_cache: bool = True,
        include_fundamentals: bool = False
    ):
        """
        Initialize stock scanner.
        
        Args:
            output_dir: Directory to save scan results
            use_cache: Enable caching to avoid re-fetching data (default: True)
            include_fundamentals: Include fundamental analysis (default: False, slower but more comprehensive)
        """
        self.dataset_collector = DatasetCollector()
        self.data_fetcher = DataFetcher(use_cache=use_cache)
        self.technical_analyzer = TechnicalAnalysisEngine()
        self.fundamental_analyzer = FundamentalAnalysisEngine() if include_fundamentals else None
        self.include_fundamentals = include_fundamentals
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"StockScanner initialized (cache: {'enabled' if use_cache else 'disabled'}, "
                   f"fundamentals: {'enabled' if include_fundamentals else 'disabled'})")

    def analyze_single_stock(
        self, 
        symbol: str, 
        include_company_info: bool = False
    ) -> Optional[Dict]:
        """
        Analyze a single stock with technical and optional fundamental analysis.
        
        Args:
            symbol: Stock ticker symbol
            include_company_info: Include company metadata
            
        Returns:
            Dictionary with analysis results or None on error
        """
        try:
            # Fetch data
            historical_df = self.data_fetcher.fetch_historical_data(symbol, days=250)
            current_data = self.data_fetcher.fetch_current_price(symbol)
            
            if historical_df is None or current_data is None:
                logger.warning(f"Could not fetch data for {symbol}")
                return None
            
            # Calculate technical indicators
            indicators = self.technical_analyzer.calculate_indicators(historical_df)
            
            if indicators is None:
                logger.warning(f"Could not calculate indicators for {symbol}")
                return None
            
            # Calculate technical score
            tech_score = self.technical_analyzer.calculate_technical_score(
                indicators, 
                current_data['current_price']
            )
            
            # Generate signal
            signal = self.technical_analyzer.generate_signal(
                indicators, 
                tech_score, 
                current_data['current_price']
            )
            
            # Build result with technical analysis
            result = {
                'symbol': symbol,
                'price': current_data['current_price'],
                'volume': current_data.get('volume', 0),
                'technical_score': tech_score.composite_score,
                'trend_score': tech_score.trend_score,
                'momentum_score': tech_score.momentum_score,
                'volatility_score': tech_score.volatility_score,
                'volume_score': tech_score.volume_score,
                'signal': signal.signal_type.value,
                'confidence': signal.confidence.value,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'risk_reward_ratio': signal.risk_reward_ratio,
                'reasons': signal.reasons[:5],  # Top 5 reasons
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            # Add fundamental analysis if enabled
            if self.include_fundamentals and self.fundamental_analyzer:
                fund_indicators = self.fundamental_analyzer.fetch_fundamentals(symbol)
                
                if fund_indicators:
                    fund_score = self.fundamental_analyzer.calculate_fundamental_score(
                        fund_indicators,
                        current_data['current_price']
                    )
                    
                    # Add fundamental metrics to result
                    result.update({
                        'fundamental_score': fund_score.composite_score,
                        'valuation_score': fund_score.valuation_score,
                        'growth_score': fund_score.growth_score,
                        'profitability_score': fund_score.profitability_score,
                        'financial_health_score': fund_score.financial_health_score,
                        'pe_ratio': fund_indicators.pe_ratio,
                        'peg_ratio': fund_indicators.peg_ratio,
                        'earnings_growth': fund_indicators.earnings_growth,
                        'revenue_growth': fund_indicators.revenue_growth,
                        'profit_margin': fund_indicators.profit_margin,
                        'roe': fund_indicators.roe,
                        'debt_to_equity': fund_indicators.debt_to_equity,
                        'analyst_target': fund_indicators.target_price,
                        'analyst_recommendation': fund_indicators.recommendation,
                        'fundamental_reasons': fund_score.reasons[:3],  # Top 3 fundamental reasons
                        
                        # Combined score (60% technical, 40% fundamental for swing trading)
                        'composite_score': (tech_score.composite_score * 0.6) + (fund_score.composite_score * 0.4)
                    })
                else:
                    # No fundamental data available
                    result.update({
                        'fundamental_score': None,
                        'composite_score': tech_score.composite_score  # Fall back to technical only
                    })
            else:
                result['composite_score'] = tech_score.composite_score
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def scan_dataset(
        self,
        dataset_name: str = "COMBINED",
        sector_filter: Optional[str] = None,
        signal_filter: Optional[str] = None,
        min_score: float = 0.0,
        max_stocks: Optional[int] = None,
        parallel: bool = True,
        max_workers: int = 5
    ) -> pd.DataFrame:
        """
        Scan an entire dataset with technical analysis.
        
        Args:
            dataset_name: Dataset to scan ('SP500', 'NASDAQ100', 'COMBINED')
            sector_filter: Filter by sector (e.g., 'Technology')
            signal_filter: Filter by signal type ('BUY', 'SELL', 'HOLD')
            min_score: Minimum technical score (0-100)
            max_stocks: Maximum number of stocks to scan
            parallel: Use parallel processing
            max_workers: Number of parallel workers
            
        Returns:
            DataFrame with scan results sorted by technical score
        """
        logger.info(f"Starting dataset scan: {dataset_name}")
        
        # Get symbols to scan
        if sector_filter:
            symbols = self.dataset_collector.get_symbols_by_sector(dataset_name, sector_filter)
            logger.info(f"Scanning {len(symbols)} stocks in {sector_filter} sector")
        else:
            df = self.dataset_collector.load_dataset(dataset_name)
            if df is None:
                logger.error("Could not load dataset")
                return pd.DataFrame()
            symbols = df['symbol'].tolist()
            logger.info(f"Scanning {len(symbols)} stocks from {dataset_name}")
        
        if max_stocks:
            symbols = symbols[:max_stocks]
            logger.info(f"Limited to {max_stocks} stocks")
        
        # Scan stocks
        results = []
        failed_count = 0
        
        if parallel:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_symbol = {
                    executor.submit(self.analyze_single_stock, symbol): symbol 
                    for symbol in symbols
                }
                
                for i, future in enumerate(as_completed(future_to_symbol), 1):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                        else:
                            failed_count += 1
                        
                        if i % 10 == 0:
                            logger.info(f"Progress: {i}/{len(symbols)} stocks analyzed ({len(results)} successful, {failed_count} failed)")
                        
                        # Rate limiting
                        time.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        failed_count += 1
        else:
            # Sequential processing
            for i, symbol in enumerate(symbols, 1):
                result = self.analyze_single_stock(symbol)
                if result:
                    results.append(result)
                else:
                    failed_count += 1
                
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(symbols)} stocks analyzed ({len(results)} successful, {failed_count} failed)")
                
                time.sleep(0.2)  # Rate limiting
        
        logger.info(f"Scan complete: {len(results)} successful, {failed_count} failed out of {len(symbols)} total stocks")
        
        if not results:
            logger.warning("No results from scan")
            return pd.DataFrame()
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Apply filters
        total_before_filter = len(results_df)
        
        if signal_filter:
            results_df = results_df[results_df['signal'] == signal_filter.upper()]
            logger.info(f"Signal filter: {len(results_df)}/{total_before_filter} stocks with {signal_filter} signal")
        
        if min_score > 0:
            results_df = results_df[results_df['technical_score'] >= min_score]
            logger.info(f"Score filter: {len(results_df)} stocks with score >= {min_score}")
        
        # Sort by technical score (descending)
        results_df = results_df.sort_values('technical_score', ascending=False)
        
        logger.success(f"Final results: {len(results_df)} stocks (started with {len(symbols)}, {len(results)} had data, {len(symbols) - len(results)} failed)")
        
        return results_df

    def get_top_picks(
        self,
        dataset_name: str = "COMBINED",
        top_n: int = 10,
        signal_type: str = "BUY",
        min_confidence: str = "MEDIUM"
    ) -> pd.DataFrame:
        """
        Get top stock picks from a dataset.
        
        Args:
            dataset_name: Dataset to scan
            top_n: Number of top picks to return
            signal_type: Signal type filter ('BUY', 'SELL', 'HOLD')
            min_confidence: Minimum confidence level ('HIGH', 'MEDIUM', 'LOW')
            
        Returns:
            DataFrame with top picks
        """
        logger.info(f"Finding top {top_n} {signal_type} picks...")
        
        # Scan dataset with filters
        results = self.scan_dataset(
            dataset_name=dataset_name,
            signal_filter=signal_type,
            parallel=True
        )
        
        if results.empty:
            logger.warning("No stocks found matching criteria")
            return pd.DataFrame()
        
        # Filter by confidence
        confidence_levels = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        min_conf_value = confidence_levels.get(min_confidence.upper(), 1)
        
        results['confidence_value'] = results['confidence'].map(confidence_levels)
        results = results[results['confidence_value'] >= min_conf_value]
        
        # Get top N
        top_picks = results.head(top_n)
        
        logger.success(f"Found {len(top_picks)} top picks")
        
        return top_picks

    def save_scan_results(
        self, 
        results: pd.DataFrame, 
        filename: str = "scan_results.csv"
    ) -> Path:
        """
        Save scan results to file.
        
        Args:
            results: DataFrame with scan results
            filename: Output filename (CSV or JSON)
            
        Returns:
            Path to saved file
        """
        filepath = self.output_dir / filename
        
        if filename.endswith('.json'):
            results.to_json(filepath, orient='records', indent=2)
        else:
            results.to_csv(filepath, index=False)
        
        logger.info(f"Saved {len(results)} results to {filepath}")
        
        return filepath

    def generate_scan_report(
        self, 
        results: pd.DataFrame, 
        dataset_name: str = "COMBINED"
    ) -> str:
        """
        Generate a formatted scan report.
        
        Args:
            results: DataFrame with scan results
            dataset_name: Name of scanned dataset
            
        Returns:
            Formatted report string
        """
        if results.empty:
            return "No results to report."
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"STOCK SCAN REPORT - {dataset_name}")
        report_lines.append(f"Timestamp: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append(f"Total Stocks Analyzed: {len(results)}")
        report_lines.append("")
        
        # Summary by signal
        signal_summary = results['signal'].value_counts()
        report_lines.append("Signal Distribution:")
        for signal, count in signal_summary.items():
            percentage = (count / len(results)) * 100
            report_lines.append(f"  {signal}: {count} ({percentage:.1f}%)")
        
        report_lines.append("")
        
        # Top BUY signals
        buy_signals = results[results['signal'] == 'BUY'].head(10)
        if not buy_signals.empty:
            report_lines.append("TOP 10 BUY SIGNALS:")
            report_lines.append("-" * 80)
            report_lines.append(f"{'Rank':<6}{'Symbol':<8}{'Score':<8}{'Confidence':<12}{'Price':<10}{'Target':<10}{'Stop':<10}")
            report_lines.append("-" * 80)
            
            for i, row in enumerate(buy_signals.itertuples(), 1):
                report_lines.append(
                    f"{i:<6}{row.symbol:<8}{row.technical_score:<8.1f}"
                    f"{row.confidence:<12}${row.price:<9.2f}"
                    f"${row.target_price:<9.2f}${row.stop_loss:<9.2f}"
                )
        
        report_lines.append("")
        
        # Score distribution
        report_lines.append("Score Distribution:")
        score_ranges = [
            (80, 100, "Strongly Bullish"),
            (60, 79, "Bullish"),
            (40, 59, "Neutral"),
            (20, 39, "Bearish"),
            (0, 19, "Strongly Bearish")
        ]
        
        for low, high, label in score_ranges:
            count = len(results[(results['technical_score'] >= low) & (results['technical_score'] <= high)])
            if count > 0:
                percentage = (count / len(results)) * 100
                report_lines.append(f"  {label} ({low}-{high}): {count} ({percentage:.1f}%)")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


if __name__ == "__main__":
    # Test the scanner
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    scanner = StockScanner()
    
    # Quick test with a few stocks
    print("\nTesting scanner with 5 stocks from S&P 500...")
    results = scanner.scan_dataset(
        dataset_name="SP500",
        max_stocks=5,
        parallel=False
    )
    
    if not results.empty:
        print("\nResults:")
        print(results[['symbol', 'price', 'technical_score', 'signal', 'confidence']].to_string())
