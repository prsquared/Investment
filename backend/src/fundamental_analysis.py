"""
Fundamental analysis engine for stock evaluation.
Fetches and analyzes financial metrics, ratios, and company fundamentals.
"""
from typing import Optional, Dict
import yfinance as yf
from loguru import logger
from datetime import datetime

try:
    from .models import FundamentalIndicators, FundamentalScore
    from .config import get_config
except ImportError:
    from models import FundamentalIndicators, FundamentalScore
    from config import get_config


class FundamentalAnalysisEngine:
    """
    Analyzes fundamental metrics for stocks.
    Uses yfinance for financial data and ratios.
    """

    def __init__(self):
        """Initialize Fundamental Analysis Engine."""
        self.config = get_config()
        logger.info("FundamentalAnalysisEngine initialized")

    def fetch_fundamentals(self, symbol: str) -> Optional[FundamentalIndicators]:
        """
        Fetch fundamental data for a stock.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            FundamentalIndicators object or None if data unavailable
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Some stocks may not have all data
            if not info or 'symbol' not in info:
                logger.warning(f"No fundamental data available for {symbol}")
                return None
            
            indicators = FundamentalIndicators(
                # Valuation Ratios
                pe_ratio=self._safe_get(info, 'trailingPE'),
                forward_pe=self._safe_get(info, 'forwardPE'),
                peg_ratio=self._safe_get(info, 'pegRatio'),
                price_to_book=self._safe_get(info, 'priceToBook'),
                price_to_sales=self._safe_get(info, 'priceToSalesTrailing12Months'),
                ev_to_ebitda=self._safe_get(info, 'enterpriseToEbitda'),
                
                # Growth Metrics
                earnings_growth=self._safe_get(info, 'earningsGrowth', multiply=100),
                revenue_growth=self._safe_get(info, 'revenueGrowth', multiply=100),
                earnings_quarterly_growth=self._safe_get(info, 'earningsQuarterlyGrowth', multiply=100),
                
                # Profitability
                profit_margin=self._safe_get(info, 'profitMargins', multiply=100),
                operating_margin=self._safe_get(info, 'operatingMargins', multiply=100),
                gross_margin=self._safe_get(info, 'grossMargins', multiply=100),
                roe=self._safe_get(info, 'returnOnEquity', multiply=100),
                roa=self._safe_get(info, 'returnOnAssets', multiply=100),
                
                # Financial Health
                debt_to_equity=self._safe_get(info, 'debtToEquity'),
                current_ratio=self._safe_get(info, 'currentRatio'),
                quick_ratio=self._safe_get(info, 'quickRatio'),
                free_cash_flow=self._safe_get(info, 'freeCashflow'),
                
                # Earnings & Dividends
                eps=self._safe_get(info, 'trailingEps'),
                dividend_yield=self._safe_get(info, 'dividendYield', multiply=100),
                payout_ratio=self._safe_get(info, 'payoutRatio', multiply=100),
                
                # Market Data
                market_cap=self._safe_get(info, 'marketCap'),
                beta=self._safe_get(info, 'beta'),
                shares_outstanding=self._safe_get(info, 'sharesOutstanding'),
                float_shares=self._safe_get(info, 'floatShares'),
                
                # Analyst Data
                target_price=self._safe_get(info, 'targetMeanPrice'),
                recommendation=self._safe_get(info, 'recommendationKey'),
                num_analysts=self._safe_get(info, 'numberOfAnalystOpinions'),
            )
            
            logger.debug(f"Fetched fundamental data for {symbol}")
            return indicators
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            return None

    def _safe_get(self, data: Dict, key: str, multiply: float = 1.0) -> Optional[float]:
        """
        Safely get value from dictionary with optional multiplication.
        
        Args:
            data: Dictionary to get value from
            key: Key to look up
            multiply: Optional multiplier (e.g., 100 to convert to percentage)
            
        Returns:
            Float value or None
        """
        value = data.get(key)
        if value is None or value == 'N/A':
            return None
        try:
            return float(value) * multiply
        except (ValueError, TypeError):
            return None

    def calculate_fundamental_score(
        self,
        indicators: FundamentalIndicators,
        current_price: float
    ) -> FundamentalScore:
        """
        Calculate composite fundamental score (0-100).
        
        Scoring criteria for swing trading:
        - Valuation: Prefer reasonable valuations (not too cheap = risky, not too expensive)
        - Growth: Strong earnings and revenue growth
        - Profitability: High margins and ROE
        - Financial Health: Low debt, good liquidity
        
        Args:
            indicators: Fundamental indicators
            current_price: Current stock price
            
        Returns:
            FundamentalScore with breakdown and composite score
        """
        scores = []
        reasons = []
        
        # 1. Valuation Score (0-100) - Weight: 30%
        valuation_score = self._score_valuation(indicators, current_price, reasons)
        scores.append(('valuation', valuation_score, 0.30))
        
        # 2. Growth Score (0-100) - Weight: 35%
        growth_score = self._score_growth(indicators, reasons)
        scores.append(('growth', growth_score, 0.35))
        
        # 3. Profitability Score (0-100) - Weight: 25%
        profitability_score = self._score_profitability(indicators, reasons)
        scores.append(('profitability', profitability_score, 0.25))
        
        # 4. Financial Health Score (0-100) - Weight: 10%
        health_score = self._score_financial_health(indicators, reasons)
        scores.append(('health', health_score, 0.10))
        
        # Calculate weighted composite score
        composite = sum(score * weight for _, score, weight in scores)
        
        return FundamentalScore(
            valuation_score=valuation_score,
            growth_score=growth_score,
            profitability_score=profitability_score,
            financial_health_score=health_score,
            composite_score=composite,
            reasons=reasons
        )

    def _score_valuation(self, ind: FundamentalIndicators, price: float, reasons: list) -> float:
        """Score valuation metrics (lower P/E, PEG is better for value)."""
        score = 50.0  # Neutral start
        
        # P/E Ratio (sweet spot: 10-25 for swing trading)
        if ind.pe_ratio is not None:
            if 10 <= ind.pe_ratio <= 20:
                score += 15
                reasons.append(f"Attractive P/E ratio: {ind.pe_ratio:.1f}")
            elif 20 < ind.pe_ratio <= 30:
                score += 10
                reasons.append(f"Reasonable P/E ratio: {ind.pe_ratio:.1f}")
            elif ind.pe_ratio > 50:
                score -= 10
                reasons.append(f"High P/E ratio: {ind.pe_ratio:.1f} (expensive)")
            elif ind.pe_ratio < 5:
                score -= 5
                reasons.append(f"Very low P/E: {ind.pe_ratio:.1f} (potential risk)")
        
        # PEG Ratio (< 1 is undervalued, 1-2 is fair)
        if ind.peg_ratio is not None:
            if ind.peg_ratio < 1.0:
                score += 15
                reasons.append(f"Undervalued PEG ratio: {ind.peg_ratio:.2f}")
            elif 1.0 <= ind.peg_ratio <= 2.0:
                score += 10
                reasons.append(f"Fair PEG ratio: {ind.peg_ratio:.2f}")
            elif ind.peg_ratio > 3.0:
                score -= 10
        
        # Price to Book (< 3 is reasonable)
        if ind.price_to_book is not None:
            if ind.price_to_book < 2.0:
                score += 10
                reasons.append(f"Good price-to-book: {ind.price_to_book:.2f}")
            elif ind.price_to_book > 5.0:
                score -= 5
        
        # Target Price vs Current Price
        if ind.target_price is not None and price > 0:
            upside = ((ind.target_price - price) / price) * 100
            if upside > 20:
                score += 10
                reasons.append(f"Analyst target upside: +{upside:.1f}%")
            elif upside > 10:
                score += 5
        
        return max(0, min(100, score))

    def _score_growth(self, ind: FundamentalIndicators, reasons: list) -> float:
        """Score growth metrics (higher is better)."""
        score = 50.0
        
        # Earnings Growth (YoY)
        if ind.earnings_growth is not None:
            if ind.earnings_growth > 25:
                score += 20
                reasons.append(f"Strong earnings growth: +{ind.earnings_growth:.1f}%")
            elif ind.earnings_growth > 15:
                score += 15
                reasons.append(f"Good earnings growth: +{ind.earnings_growth:.1f}%")
            elif ind.earnings_growth > 5:
                score += 5
            elif ind.earnings_growth < -10:
                score -= 15
                reasons.append(f"Declining earnings: {ind.earnings_growth:.1f}%")
        
        # Revenue Growth
        if ind.revenue_growth is not None:
            if ind.revenue_growth > 20:
                score += 15
                reasons.append(f"Strong revenue growth: +{ind.revenue_growth:.1f}%")
            elif ind.revenue_growth > 10:
                score += 10
            elif ind.revenue_growth < 0:
                score -= 10
                reasons.append(f"Revenue declining: {ind.revenue_growth:.1f}%")
        
        # Quarterly Earnings Growth
        if ind.earnings_quarterly_growth is not None:
            if ind.earnings_quarterly_growth > 20:
                score += 15
                reasons.append(f"Accelerating quarterly earnings: +{ind.earnings_quarterly_growth:.1f}%")
            elif ind.earnings_quarterly_growth > 10:
                score += 10
        
        return max(0, min(100, score))

    def _score_profitability(self, ind: FundamentalIndicators, reasons: list) -> float:
        """Score profitability metrics (higher margins and ROE is better)."""
        score = 50.0
        
        # Profit Margin
        if ind.profit_margin is not None:
            if ind.profit_margin > 20:
                score += 15
                reasons.append(f"Excellent profit margin: {ind.profit_margin:.1f}%")
            elif ind.profit_margin > 10:
                score += 10
                reasons.append(f"Good profit margin: {ind.profit_margin:.1f}%")
            elif ind.profit_margin < 0:
                score -= 20
                reasons.append(f"Unprofitable: {ind.profit_margin:.1f}% margin")
        
        # Return on Equity
        if ind.roe is not None:
            if ind.roe > 20:
                score += 15
                reasons.append(f"Strong ROE: {ind.roe:.1f}%")
            elif ind.roe > 15:
                score += 10
            elif ind.roe < 5:
                score -= 10
        
        # Operating Margin
        if ind.operating_margin is not None:
            if ind.operating_margin > 20:
                score += 10
                reasons.append(f"High operating margin: {ind.operating_margin:.1f}%")
            elif ind.operating_margin < 5:
                score -= 10
        
        # Gross Margin
        if ind.gross_margin is not None:
            if ind.gross_margin > 50:
                score += 10
        
        return max(0, min(100, score))

    def _score_financial_health(self, ind: FundamentalIndicators, reasons: list) -> float:
        """Score financial health (low debt, high liquidity is better)."""
        score = 50.0
        
        # Debt to Equity
        if ind.debt_to_equity is not None:
            if ind.debt_to_equity < 50:
                score += 20
                reasons.append(f"Low debt-to-equity: {ind.debt_to_equity:.1f}")
            elif ind.debt_to_equity < 100:
                score += 10
            elif ind.debt_to_equity > 200:
                score -= 15
                reasons.append(f"High debt-to-equity: {ind.debt_to_equity:.1f}")
        
        # Current Ratio (> 1.5 is healthy)
        if ind.current_ratio is not None:
            if ind.current_ratio > 2.0:
                score += 15
                reasons.append(f"Strong liquidity: {ind.current_ratio:.2f} current ratio")
            elif ind.current_ratio > 1.5:
                score += 10
            elif ind.current_ratio < 1.0:
                score -= 15
                reasons.append(f"Weak liquidity: {ind.current_ratio:.2f} current ratio")
        
        # Free Cash Flow (positive is good)
        if ind.free_cash_flow is not None:
            if ind.free_cash_flow > 0:
                score += 15
                reasons.append(f"Positive free cash flow: ${ind.free_cash_flow/1e9:.2f}B")
            else:
                score -= 10
                reasons.append(f"Negative free cash flow")
        
        return max(0, min(100, score))

    def get_analyst_consensus(self, symbol: str) -> Optional[str]:
        """
        Get analyst recommendation consensus.
        
        Returns:
            String like "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('recommendationKey', None)
        except:
            return None


if __name__ == "__main__":
    # Test the fundamental analysis
    engine = FundamentalAnalysisEngine()
    
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"Fundamental Analysis: {symbol}")
        print('='*60)
        
        indicators = engine.fetch_fundamentals(symbol)
        if indicators:
            print(f"\n📊 Valuation:")
            print(f"  P/E Ratio: {indicators.pe_ratio:.2f}" if indicators.pe_ratio else "  P/E Ratio: N/A")
            print(f"  PEG Ratio: {indicators.peg_ratio:.2f}" if indicators.peg_ratio else "  PEG Ratio: N/A")
            print(f"  Price/Book: {indicators.price_to_book:.2f}" if indicators.price_to_book else "  Price/Book: N/A")
            
            print(f"\n📈 Growth:")
            print(f"  Earnings Growth: {indicators.earnings_growth:.1f}%" if indicators.earnings_growth else "  Earnings Growth: N/A")
            print(f"  Revenue Growth: {indicators.revenue_growth:.1f}%" if indicators.revenue_growth else "  Revenue Growth: N/A")
            
            print(f"\n💰 Profitability:")
            print(f"  Profit Margin: {indicators.profit_margin:.1f}%" if indicators.profit_margin else "  Profit Margin: N/A")
            print(f"  ROE: {indicators.roe:.1f}%" if indicators.roe else "  ROE: N/A")
            
            print(f"\n🏦 Financial Health:")
            print(f"  Debt/Equity: {indicators.debt_to_equity:.1f}" if indicators.debt_to_equity else "  Debt/Equity: N/A")
            print(f"  Current Ratio: {indicators.current_ratio:.2f}" if indicators.current_ratio else "  Current Ratio: N/A")
            
            # Get current price (dummy for testing)
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            current_price = ticker.info.get('currentPrice', 100)
            
            score = engine.calculate_fundamental_score(indicators, current_price)
            print(f"\n🎯 Fundamental Score: {score.composite_score:.1f}/100")
            print(f"  Valuation: {score.valuation_score:.1f}")
            print(f"  Growth: {score.growth_score:.1f}")
            print(f"  Profitability: {score.profitability_score:.1f}")
            print(f"  Financial Health: {score.financial_health_score:.1f}")
            
            print(f"\n📝 Key Reasons:")
            for reason in score.reasons[:5]:
                print(f"  • {reason}")
