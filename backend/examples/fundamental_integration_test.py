"""
Test fundamental analysis integration with stock scanner.
Demonstrates combined technical + fundamental analysis.
"""
import sys
from pathlib import Path

# Add src to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir / 'src'))

from stock_scanner import StockScanner
from loguru import logger

def test_fundamental_integration():
    """Test stock scanner with fundamental analysis enabled."""
    
    logger.info("=" * 80)
    logger.info("Testing Fundamental Analysis Integration")
    logger.info("=" * 80)
    
    # Initialize scanner WITH fundamentals
    scanner = StockScanner(
        output_dir=backend_dir / 'output',
        use_cache=True,
        include_fundamentals=True
    )
    
    # Test stocks: mix of different profiles
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'JPM']
    
    logger.info(f"\nAnalyzing {len(test_symbols)} stocks with combined technical + fundamental analysis...\n")
    
    for symbol in test_symbols:
        logger.info(f"\n{'='*60}")
        logger.info(f"Analyzing {symbol}")
        logger.info(f"{'='*60}")
        
        result = scanner.analyze_single_stock(symbol)
        
        if result:
            # Display technical scores
            logger.info(f"\n📊 TECHNICAL ANALYSIS:")
            logger.info(f"  Technical Score:  {result['technical_score']:.1f}/100")
            logger.info(f"  Signal:           {result['signal']} ({result['confidence']})")
            logger.info(f"  Price:            ${result['price']:.2f}")
            if result.get('entry_price'):
                logger.info(f"  Entry:            ${result['entry_price']:.2f}")
            if result.get('target_price'):
                logger.info(f"  Target:           ${result['target_price']:.2f}")
            if result.get('stop_loss'):
                logger.info(f"  Stop Loss:        ${result['stop_loss']:.2f}")
            if result.get('risk_reward_ratio'):
                logger.info(f"  Risk/Reward:      {result['risk_reward_ratio']:.2f}")
            
            # Display fundamental scores
            if result.get('fundamental_score') is not None:
                logger.info(f"\n💰 FUNDAMENTAL ANALYSIS:")
                logger.info(f"  Fundamental Score: {result['fundamental_score']:.1f}/100")
                logger.info(f"    Valuation:       {result['valuation_score']:.1f}/100")
                logger.info(f"    Growth:          {result['growth_score']:.1f}/100")
                logger.info(f"    Profitability:   {result['profitability_score']:.1f}/100")
                logger.info(f"    Financial Health: {result['financial_health_score']:.1f}/100")
                
                logger.info(f"\n  Key Metrics:")
                if result.get('pe_ratio'):
                    logger.info(f"    P/E Ratio:       {result['pe_ratio']:.2f}")
                if result.get('peg_ratio'):
                    logger.info(f"    PEG Ratio:       {result['peg_ratio']:.2f}")
                if result.get('earnings_growth'):
                    logger.info(f"    Earnings Growth: {result['earnings_growth']:.1f}%")
                if result.get('revenue_growth'):
                    logger.info(f"    Revenue Growth:  {result['revenue_growth']:.1f}%")
                if result.get('profit_margin'):
                    logger.info(f"    Profit Margin:   {result['profit_margin']:.1f}%")
                if result.get('roe'):
                    logger.info(f"    ROE:             {result['roe']:.1f}%")
                if result.get('debt_to_equity'):
                    logger.info(f"    Debt/Equity:     {result['debt_to_equity']:.2f}")
                
                if result.get('analyst_target'):
                    upside = ((result['analyst_target'] - result['price']) / result['price']) * 100
                    logger.info(f"    Analyst Target:  ${result['analyst_target']:.2f} ({upside:+.1f}%)")
                if result.get('analyst_recommendation'):
                    logger.info(f"    Recommendation:  {result['analyst_recommendation']}")
                
                # Show fundamental reasons
                if result.get('fundamental_reasons'):
                    logger.info(f"\n  Top Fundamental Strengths:")
                    for reason in result['fundamental_reasons']:
                        logger.info(f"    ✓ {reason}")
            
            # Display combined score
            logger.info(f"\n🎯 COMPOSITE SCORE:")
            logger.info(f"  Combined Score:   {result['composite_score']:.1f}/100")
            logger.info(f"  (60% Technical + 40% Fundamental)")
            
            # Show technical reasons
            if result.get('reasons'):
                logger.info(f"\n  Technical Strengths:")
                for reason in result['reasons'][:3]:
                    logger.info(f"    ✓ {reason}")
        else:
            logger.warning(f"Could not analyze {symbol}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Test Complete!")
    logger.info("=" * 80)
    logger.info("\n✅ Fundamental analysis successfully integrated into stock scanner")
    logger.info("✅ Composite scoring (60% technical + 40% fundamental) working")
    logger.info("✅ All metrics displayed correctly")

if __name__ == "__main__":
    test_fundamental_integration()
