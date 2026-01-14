"""
Example: Technical Analysis Workflow
Demonstrates how to analyze stocks using the technical analysis engine.
"""
import sys
from pathlib import Path
from loguru import logger
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalysisEngine
from models import StockData
from config import get_config


def setup_logging():
    """Configure logging."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/technical_analysis.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def analyze_stock(symbol: str) -> dict:
    """
    Complete technical analysis workflow for a single stock.

    Args:
        symbol: Stock ticker symbol

    Returns:
        Dictionary with complete analysis results
    """
    logger.info(f"=" * 80)
    logger.info(f"Analyzing {symbol}")
    logger.info(f"=" * 80)

    # Initialize components
    fetcher = DataFetcher()
    analyzer = TechnicalAnalysisEngine()
    config = get_config()

    # Step 1: Fetch historical data
    logger.info(f"Step 1: Fetching historical data...")
    historical_df = fetcher.fetch_historical_data(
        symbol,
        days=config.technical_analysis.min_historical_days + 50  # Extra buffer
    )

    if historical_df is None or len(historical_df) < config.technical_analysis.min_historical_days:
        logger.error(f"Insufficient historical data for {symbol}")
        return {'error': 'Insufficient data'}

    logger.success(f"Fetched {len(historical_df)} days of data")

    # Step 2: Fetch current price data
    logger.info(f"Step 2: Fetching current price...")
    current_data = fetcher.fetch_current_price(symbol)

    if current_data is None:
        logger.error(f"Could not fetch current price for {symbol}")
        return {'error': 'No current price data'}

    logger.success(f"Current price: ${current_data['current_price']:.2f}")

    # Step 3: Calculate technical indicators
    logger.info(f"Step 3: Calculating technical indicators...")
    indicators = analyzer.calculate_indicators(historical_df)

    logger.success("Technical indicators calculated")
    logger.info(f"  RSI(14): {indicators.rsi14:.2f}" if indicators.rsi14 else "  RSI: N/A")
    logger.info(f"  SMA(20): ${indicators.sma20:.2f}" if indicators.sma20 else "  SMA(20): N/A")
    logger.info(f"  SMA(50): ${indicators.sma50:.2f}" if indicators.sma50 else "  SMA(50): N/A")
    logger.info(f"  SMA(200): ${indicators.sma200:.2f}" if indicators.sma200 else "  SMA(200): N/A")
    logger.info(f"  MACD: {indicators.macd:.3f}" if indicators.macd else "  MACD: N/A")

    # Step 4: Calculate technical score
    logger.info(f"Step 4: Calculating technical score...")
    tech_score = analyzer.calculate_technical_score(
        indicators,
        current_data['current_price']
    )

    logger.success(f"Technical Score: {tech_score.composite_score:.2f}/100")
    logger.info(f"  Trend: {tech_score.trend_score:.1f}")
    logger.info(f"  Momentum: {tech_score.momentum_score:.1f}")
    logger.info(f"  Volatility: {tech_score.volatility_score:.1f}")
    logger.info(f"  Volume: {tech_score.volume_score:.1f}")

    # Step 5: Generate trading signal
    logger.info(f"Step 5: Generating trading signal...")
    signal = analyzer.generate_signal(
        indicators,
        tech_score,
        current_data['current_price']
    )

    logger.success(f"Signal: {signal.signal_type.value} ({signal.confidence.value})")
    if signal.target_price:
        logger.info(f"  Entry: ${signal.entry_price:.2f}")
        logger.info(f"  Target: ${signal.target_price:.2f}")
        logger.info(f"  Stop Loss: ${signal.stop_loss:.2f}")

        # Calculate risk/reward ratio
        if signal.signal_type.value == "BUY":
            risk = signal.entry_price - signal.stop_loss
            reward = signal.target_price - signal.entry_price
            rr_ratio = reward / risk if risk > 0 else 0
            logger.info(f"  Risk/Reward: 1:{rr_ratio:.2f}")

    # Step 6: Create complete stock data object
    stock_data = StockData(
        symbol=symbol,
        current_price=current_data['current_price'],
        open_price=current_data['open_price'],
        high_price=current_data['high_price'],
        low_price=current_data['low_price'],
        close_price=current_data['close_price'],
        volume=current_data['volume'],
        timestamp=current_data['timestamp'],
        technical_indicators=indicators,
        technical_score=tech_score,
        trading_signal=signal,
        market_cap=current_data.get('market_cap'),
    )

    # Step 7: Display key reasons
    logger.info(f"\nKey Analysis Reasons:")
    for i, reason in enumerate(signal.reasons[:5], 1):
        logger.info(f"  {i}. {reason}")

    logger.info(f"=" * 80)

    return stock_data.to_dict()


def analyze_multiple_stocks(symbols: list[str]) -> dict[str, dict]:
    """
    Analyze multiple stocks and rank them.

    Args:
        symbols: List of stock ticker symbols

    Returns:
        Dictionary of analysis results, sorted by score
    """
    results = {}

    for symbol in symbols:
        try:
            result = analyze_stock(symbol)
            if 'error' not in result:
                results[symbol] = result
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    # Sort by technical score
    sorted_results = dict(
        sorted(
            results.items(),
            key=lambda x: x[1].get('technical_score', {}).get('composite_score', 0),
            reverse=True
        )
    )

    # Display rankings
    logger.info("\n" + "=" * 80)
    logger.info("STOCK RANKINGS (by Technical Score)")
    logger.info("=" * 80)

    for rank, (symbol, data) in enumerate(sorted_results.items(), 1):
        score = data.get('technical_score', {}).get('composite_score', 0)
        signal = data.get('trading_signal', {}).get('signal', 'HOLD')
        confidence = data.get('trading_signal', {}).get('confidence', 'LOW')
        price = data.get('price_data', {}).get('current', 0)

        logger.info(
            f"{rank}. {symbol:6} | Score: {score:5.1f} | "
            f"Signal: {signal:4} ({confidence:6}) | "
            f"Price: ${price:7.2f}"
        )

    logger.info("=" * 80)

    return sorted_results


def main():
    """Main execution."""
    setup_logging()

    logger.info("Technical Analysis Example - Stock Selection System")
    logger.info("")

    # Example 1: Analyze a single stock
    logger.info("EXAMPLE 1: Single Stock Analysis")
    result = analyze_stock("AAPL")

    # Save result to file
    output_file = Path("output") / "aapl_analysis.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(f"\nAnalysis saved to: {output_file}")

    # Example 2: Analyze multiple stocks
    logger.info("\n\nEXAMPLE 2: Multiple Stock Analysis")
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

    results = analyze_multiple_stocks(symbols)

    # Save results
    output_file = Path("output") / "multi_stock_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"\nResults saved to: {output_file}")

    # Display top pick
    if results:
        top_symbol = list(results.keys())[0]
        top_data = results[top_symbol]

        logger.info("\n" + "=" * 80)
        logger.info("TOP PICK FOR SWING TRADING")
        logger.info("=" * 80)
        logger.info(f"Symbol: {top_symbol}")
        logger.info(f"Technical Score: {top_data['technical_score']['composite_score']:.1f}/100")
        logger.info(f"Signal: {top_data['trading_signal']['signal']} "
                   f"({top_data['trading_signal']['confidence']})")

        if top_data['trading_signal'].get('target_price'):
            logger.info(f"Entry: ${top_data['trading_signal']['entry_price']:.2f}")
            logger.info(f"Target: ${top_data['trading_signal']['target_price']:.2f}")
            logger.info(f"Stop Loss: ${top_data['trading_signal']['stop_loss']:.2f}")

        logger.info("\nTop Reasons:")
        for i, reason in enumerate(top_data['trading_signal']['reasons'][:3], 1):
            logger.info(f"  {i}. {reason}")

        logger.info("=" * 80)


if __name__ == "__main__":
    main()

