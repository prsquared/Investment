# Technical Analysis Quick Reference

## Signal Interpretation Guide

### Technical Score Ranges

| Score Range | Interpretation | Action |
|------------|----------------|--------|
| 80-100 | Strongly Bullish | Strong BUY (High Confidence) |
| 70-79 | Bullish | BUY (Medium Confidence) |
| 55-69 | Moderately Bullish | BUY (Low Confidence) |
| 45-54 | Neutral | HOLD |
| 31-44 | Moderately Bearish | HOLD/Watch |
| 21-30 | Bearish | SELL (Medium Confidence) |
| 0-20 | Strongly Bearish | Strong SELL (High Confidence) |

## Technical Indicators Cheat Sheet

### Moving Averages (Trend)

**Bullish Signals:**
- Price > SMA(20) > SMA(50) > SMA(200)
- EMA(12) crosses above EMA(26)
- Price bounces off SMA(50) support

**Bearish Signals:**
- Price < SMA(20) < SMA(50) < SMA(200)
- EMA(12) crosses below EMA(26)
- Price rejected at SMA(50) resistance

### RSI (Momentum)

| RSI Value | Interpretation | Trading Action |
|-----------|----------------|----------------|
| > 70 | Overbought | Consider selling/taking profits |
| 50-70 | Bullish | Look for entry on pullback |
| 40-50 | Neutral | Wait for clearer signal |
| 30-40 | Oversold territory | Watch for reversal |
| < 30 | Oversold | Potential buying opportunity |

**Divergence:**
- Bullish: Price makes lower low, RSI makes higher low → Reversal up
- Bearish: Price makes higher high, RSI makes lower high → Reversal down

### MACD (Momentum & Trend)

**Bullish Signals:**
- MACD line crosses above signal line
- Histogram turns positive
- MACD crosses above zero line

**Bearish Signals:**
- MACD line crosses below signal line
- Histogram turns negative
- MACD crosses below zero line

### Bollinger Bands (Volatility)

**Price Position:**
- Near Lower Band: Potential bounce (oversold)
- Near Upper Band: Potential pullback (overbought)
- Middle Band: Fair value, trend continuation
- Outside Bands: Extreme move, expect reversal

**Band Width:**
- Narrow bands: Low volatility → Breakout coming
- Wide bands: High volatility → Consolidation coming

### ATR (Volatility)

**For Swing Trading:**
- ATR 2-3% of price: Ideal (enough movement)
- ATR < 2%: Too quiet, low profit potential
- ATR > 5%: Too volatile, higher risk

**Position Sizing:**
- Stop Loss: 1-1.5 × ATR below entry
- Target: 2-3 × ATR above entry
- Risk/Reward: Minimum 1:2 ratio

### Volume Analysis

| Volume Ratio | Interpretation | Significance |
|--------------|----------------|--------------|
| > 2.0x | Volume spike | Strong conviction, confirm trend |
| 1.2-2.0x | Above average | Good confirmation |
| 0.8-1.2x | Normal | Neutral |
| < 0.8x | Below average | Weak signal, low conviction |

## Swing Trading Entry Patterns

### High Probability Setups

1. **Pullback to Support**
   - Strong uptrend (SMA alignment)
   - Price pulls back to SMA(20) or SMA(50)
   - RSI 40-50 (not overbought)
   - Volume decreases on pullback
   - Entry: Bounce off MA with volume

2. **Breakout**
   - Consolidation with tightening BBands
   - Low volume during consolidation
   - Entry: Break above resistance with volume spike (>2x)
   - Stop below consolidation

3. **Oversold Bounce**
   - RSI < 30
   - Price at lower Bollinger Band
   - MACD showing bullish divergence
   - Entry: RSI turns up, price crosses SMA(20)

4. **Trend Continuation**
   - Strong trend (price > all MAs)
   - Brief consolidation
   - MACD positive, RSI 50-65
   - Entry: Break of consolidation high

## Exit Strategies

### Take Profit Targets

**Conservative (1:1.5 R/R):**
- Target: Entry + (1.5 × ATR)
- Good for lower confidence signals

**Moderate (1:2 R/R):**
- Target: Entry + (2 × ATR)
- Standard for medium confidence

**Aggressive (1:3 R/R):**
- Target: Entry + (3 × ATR)
- Only for high confidence, strong trend

### Stop Loss Placement

**Tight (Scalping style):**
- Stop: Entry - (0.5 × ATR)
- High win rate needed

**Standard (Swing trading):**
- Stop: Entry - (1 × ATR)
- Balanced approach

**Wide (Position trading):**
- Stop: Entry - (1.5-2 × ATR)
- Lower win rate OK, big winners

### Trailing Stops

Once in profit:
1. Move stop to breakeven at +1 ATR profit
2. Trail stop by 0.5 ATR increments
3. Or use SMA(20) as trailing stop

## Risk Management Rules

### Position Sizing

**Risk per Trade:** 1-2% of portfolio
```
Position Size = (Account × Risk%) / (Entry - Stop Loss)
```

**Example:**
- Account: $50,000
- Risk: 1% = $500
- Entry: $100
- Stop: $95
- Position Size: $500 / $5 = 100 shares

### Portfolio Limits

- Max 5-10 positions simultaneously
- No more than 20% in one sector
- Keep 20-30% cash for opportunities

## Common Mistakes to Avoid

❌ **Don't:**
- Chase stocks after big moves
- Ignore stop losses
- Trade against strong trends
- Use too much leverage
- Hold losing positions hoping for recovery
- Enter without clear plan

✅ **Do:**
- Wait for pullbacks in uptrends
- Always use stop losses
- Trade with the trend
- Keep position sizes manageable
- Cut losses quickly
- Have entry and exit plan before trading

## Example Trade Plan Template

```
Symbol: AAPL
Date: 2026-01-14
Analysis: Strong uptrend, pullback to SMA(50)

Technical Score: 75/100
- Trend: 85 (Bullish MA alignment)
- Momentum: 70 (RSI 55, MACD positive)
- Volatility: 75 (Ideal ATR 3.2%)
- Volume: 70 (Normal volume)

Signal: BUY (Medium Confidence)

Entry: $182.50 (at SMA50 support)
Target: $191.00 (+4.7%, 2.5 ATR)
Stop Loss: $179.00 (-1.9%, 1 ATR)
Risk/Reward: 1:2.4

Position Size: 100 shares ($18,250)
Risk: $350 (1% of $35,000 account)

Exit Plan:
- Move to breakeven at $185.50
- Take 50% profit at $188.00
- Trail stop on remaining 50%
```

## Resources

### Key Metrics Summary

```python
# Check these before every trade
✓ Technical Score > 55 for BUY
✓ Volume > 500K daily average
✓ Price > $5 (avoid penny stocks)
✓ ATR between 2-5% of price
✓ Clear trend direction
✓ Risk/Reward > 1:2
```

### Daily Workflow

1. **Morning (Pre-market 9:00 AM ET)**
   - Scan watchlist for high scores
   - Check overnight news
   - Identify potential setups

2. **Market Open (9:30 AM ET)**
   - Wait 15-30 minutes for settling
   - Confirm signals with volume
   - Place orders with stops

3. **During Market Hours**
   - Monitor positions
   - Adjust stops if needed
   - Don't overtrade

4. **End of Day (4:00 PM ET)**
   - Review trades
   - Update watchlist
   - Plan for tomorrow

---

**Remember:** The best trade is sometimes no trade. Wait for high-probability setups!

