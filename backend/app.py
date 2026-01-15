"""
Streamlit Dashboard for Stock Selection System
Swing Trading Analysis - Technical Indicators
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.stock_scanner import StockScanner
from src.data_fetcher import DataFetcher
from src.technical_analysis import TechnicalAnalysisEngine
from src.dataset_collector import DatasetCollector
from src.intraday_scanner import IntradayScanner, IntradaySignal
from src.premarket_scanner import PreMarketScanner, PreMarketSignal
from src.premarket_scanner import PreMarketScanner, PreMarketSignal

# Page configuration
st.set_page_config(
    page_title="Stock Scanner - Swing Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .buy-signal {
        color: #00cc00;
        font-weight: bold;
    }
    .sell-signal {
        color: #cc0000;
        font-weight: bold;
    }
    .hold-signal {
        color: #ff9900;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None
if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = None
if 'selected_row_index' not in st.session_state:
    st.session_state.selected_row_index = None

def get_currency_symbol(symbol):
    """Return ₹ for Indian stocks (.NS), $ for others."""
    return '₹' if '.NS' in str(symbol) else '$'

def color_score(val):
    """Apply color to score values."""
    try:
        # Extract numeric value from formatted string
        num_val = float(val.replace('$', '').replace('₹', '').replace('%', '').replace(',', ''))
        if num_val >= 70:
            color = '#28a745'  # Green
        elif num_val >= 50:
            color = '#ffc107'  # Orange
        else:
            color = '#dc3545'  # Red
        return f'color: {color}; font-weight: bold'
    except:
        return ''

def color_signal(val):
    """Apply color to signal column."""
    if val == 'BUY':
        return 'color: #28a745; font-weight: bold'  # Green
    elif val == 'SELL':
        return 'color: #dc3545; font-weight: bold'  # Red
    elif val == 'HOLD':
        return 'color: #ffc107; font-weight: bold'  # Orange
    return ''

def color_confidence(val):
    """Apply color to confidence column."""
    if val == 'HIGH':
        return 'color: #28a745; font-weight: bold'  # Green
    elif val == 'MEDIUM':
        return 'color: #ffc107; font-weight: bold'  # Orange
    elif val == 'LOW':
        return 'color: #dc3545; font-weight: bold'  # Red
    return ''

def save_scan_results(results, scan_params):
    """Save scan results to cache file."""
    cache_dir = Path(__file__).parent / 'data' / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / 'scan_results_cache.parquet'
    metadata_file = cache_dir / 'scan_results_metadata.json'
    
    # Save results
    results.to_parquet(cache_file, index=False)
    
    # Save metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'scan_params': scan_params,
        'num_results': len(results)
    }
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

def load_cached_scan_results():
    """Load scan results from cache if available."""
    cache_file = Path(__file__).parent / 'data' / 'cache' / 'scan_results_cache.parquet'
    metadata_file = Path(__file__).parent / 'data' / 'cache' / 'scan_results_metadata.json'
    
    if not cache_file.exists() or not metadata_file.exists():
        return None, None
    
    try:
        # Load results
        results = pd.read_parquet(cache_file)
        
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return results, metadata
    except Exception as e:
        return None, None

@st.cache_resource
def get_scanner(include_fundamentals=False):
    """Initialize scanner (cached)."""
    return StockScanner(use_cache=True, include_fundamentals=include_fundamentals)

@st.cache_resource
def get_dataset_collector():
    """Initialize dataset collector (cached)."""
    return DatasetCollector()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_datasets():
    """Load available datasets."""
    collector = get_dataset_collector()
    datasets = {}
    try:
        datasets['SP500'] = collector.load_dataset('SP500')
        datasets['NASDAQ100'] = collector.load_dataset('NASDAQ100')
        datasets['COMBINED'] = collector.load_dataset('COMBINED')
        datasets['NIFTY50'] = collector.load_dataset('NIFTY50')
        datasets['NIFTYNEXT50'] = collector.load_dataset('NIFTYNEXT50')
        datasets['NIFTYMIDCAP'] = collector.load_dataset('NIFTYMIDCAP')
        datasets['NIFTY_ALL'] = collector.load_dataset('NIFTY_ALL')
        datasets['ALL'] = collector.load_dataset('ALL')
    except FileNotFoundError:
        # Datasets don't exist, fetch them
        collector.fetch_all_datasets()
        datasets['SP500'] = collector.load_dataset('SP500')
        datasets['NASDAQ100'] = collector.load_dataset('NASDAQ100')
        datasets['COMBINED'] = collector.load_dataset('COMBINED')
        datasets['NIFTY50'] = collector.load_dataset('NIFTY50')
        datasets['NIFTYNEXT50'] = collector.load_dataset('NIFTYNEXT50')
        datasets['NIFTYMIDCAP'] = collector.load_dataset('NIFTYMIDCAP')
        datasets['NIFTY_ALL'] = collector.load_dataset('NIFTY_ALL')
        datasets['ALL'] = collector.load_dataset('ALL')
    return datasets

def get_sectors(dataset_name):
    """Get unique sectors from dataset."""
    datasets = load_datasets()
    if dataset_name in datasets and 'sector' in datasets[dataset_name].columns:
        sectors = datasets[dataset_name]['sector'].dropna().unique().tolist()
        return sorted([s for s in sectors if s])
    return []

def scan_stocks(dataset_name, sector_filter, signal_filter, min_score, max_stocks, include_fundamentals=False):
    """Run stock scan with filters."""
    scanner = get_scanner(include_fundamentals=include_fundamentals)
    
    # Get total stocks in dataset
    collector = get_dataset_collector()
    dataset_df = collector.load_dataset(dataset_name)
    total_in_dataset = len(dataset_df) if dataset_df is not None else 0
    
    scan_msg = f"Scanning {dataset_name} stocks with {'technical + fundamental' if include_fundamentals else 'technical'} analysis..."
    with st.spinner(scan_msg):
        results = scanner.scan_dataset(
            dataset_name=dataset_name,
            sector_filter=sector_filter if sector_filter != "All" else None,
            signal_filter=signal_filter if signal_filter != "All" else None,
            min_score=min_score,
            max_stocks=max_stocks,
            parallel=True
        )
    
    # Save to cache
    scan_params = {
        'dataset': dataset_name,
        'sector': sector_filter,
        'signal': signal_filter,
        'min_score': min_score,
        'max_stocks': max_stocks,
        'include_fundamentals': include_fundamentals,
        'total_in_dataset': total_in_dataset,
        'stocks_with_data': len(results)
    }
    save_scan_results(results, scan_params)
    
    return results

def plot_stock_chart(symbol, days=90):
    """Create interactive candlestick chart with indicators."""
    fetcher = DataFetcher(use_cache=True)
    analyzer = TechnicalAnalysisEngine()
    
    # Fetch data
    df = fetcher.fetch_historical_data(symbol, days=days)
    if df is None or len(df) == 0:
        st.error(f"No data available for {symbol}")
        return None
    
    # Calculate indicators
    indicators = analyzer.calculate_indicators(df)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} Price & Moving Averages', 'RSI', 'Volume'),
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Moving averages
    if indicators.sma20 is not None:
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.sma20, name='SMA 20', 
                      line=dict(color='orange', width=1)),
            row=1, col=1
        )
    if indicators.sma50 is not None:
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.sma50, name='SMA 50',
                      line=dict(color='blue', width=1)),
            row=1, col=1
        )
    if indicators.sma200 is not None:
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.sma200, name='SMA 200',
                      line=dict(color='purple', width=1)),
            row=1, col=1
        )
    
    # Bollinger Bands
    if indicators.bb_upper is not None and indicators.bb_lower is not None:
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.bb_upper, name='BB Upper',
                      line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.bb_lower, name='BB Lower',
                      line=dict(color='gray', width=1, dash='dash'),
                      fill='tonexty', fillcolor='rgba(128,128,128,0.1)'),
            row=1, col=1
        )
    
    # RSI
    if indicators.rsi14 is not None:
        fig.add_trace(
            go.Scatter(x=df.index, y=indicators.rsi14, name='RSI',
                      line=dict(color='purple', width=2)),
            row=2, col=1
        )
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, opacity=0.5)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, opacity=0.5)
    
    # Volume
    colors = ['red' if df['close'].iloc[i] < df['open'].iloc[i] else 'green' 
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], name='Volume', marker_color=colors),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )
    
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Volume", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    
    return fig

def display_stock_detail(row):
    """Display detailed stock information."""
    currency = get_currency_symbol(row['symbol'])
    st.markdown(f"### 📊 {row['symbol']} - {currency}{row['price']:.2f}")
    
    # Check if fundamentals are included
    has_fundamentals = 'fundamental_score' in row and pd.notna(row.get('fundamental_score'))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        signal_class = f"{row['signal'].lower()}-signal"
        st.markdown(f"**Signal:** <span class='{signal_class}'>{row['signal']}</span>", 
                   unsafe_allow_html=True)
        st.metric("Technical Score", f"{row['technical_score']:.1f}/100")
    
    with col2:
        st.metric("Confidence", row['confidence'])
        if has_fundamentals:
            st.metric("Fundamental Score", f"{row['fundamental_score']:.1f}/100")
        else:
            st.metric("Entry Price", f"{currency}{row['entry_price']:.2f}")
    
    with col3:
        if has_fundamentals:
            st.metric("Composite Score", f"{row['composite_score']:.1f}/100",
                     help="60% Technical + 40% Fundamental")
        else:
            target_pct = ((row['target_price']/row['entry_price'])-1)*100
            st.metric("Target Price", f"{currency}{row['target_price']:.2f}", 
                     f"+{target_pct:.1f}%")
    
    with col4:
        if has_fundamentals and row.get('entry_price'):
            st.metric("Entry Price", f"{currency}{row['entry_price']:.2f}")
        else:
            stop_pct = ((row['stop_loss']/row['entry_price'])-1)*100
            st.metric("Stop Loss", f"{currency}{row['stop_loss']:.2f}",
                     f"{stop_pct:.1f}%")
    
    # Score breakdown
    st.markdown("#### Technical Score Breakdown")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Trend", f"{row['trend_score']:.0f}")
    col2.metric("Momentum", f"{row['momentum_score']:.0f}")
    col3.metric("Volatility", f"{row['volatility_score']:.0f}")
    col4.metric("Volume", f"{row['volume_score']:.0f}")
    
    # Fundamental breakdown (if available)
    if has_fundamentals:
        st.markdown("#### Fundamental Score Breakdown")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Valuation", f"{row['valuation_score']:.0f}")
        col2.metric("Growth", f"{row['growth_score']:.0f}")
        col3.metric("Profitability", f"{row['profitability_score']:.0f}")
        col4.metric("Financial Health", f"{row['financial_health_score']:.0f}")
        
        st.markdown("#### Key Fundamental Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        if pd.notna(row.get('pe_ratio')):
            col1.metric("P/E Ratio", f"{row['pe_ratio']:.1f}")
        if pd.notna(row.get('peg_ratio')):
            col2.metric("PEG Ratio", f"{row['peg_ratio']:.2f}")
        if pd.notna(row.get('earnings_growth')):
            col3.metric("Earnings Growth", f"{row['earnings_growth']:.1f}%")
        if pd.notna(row.get('profit_margin')):
            col4.metric("Profit Margin", f"{row['profit_margin']:.1f}%")
        if pd.notna(row.get('roe')):
            col5.metric("ROE", f"{row['roe']:.1f}%")
        
        col1, col2, col3 = st.columns(3)
        if pd.notna(row.get('debt_to_equity')):
            col1.metric("Debt/Equity", f"{row['debt_to_equity']:.2f}")
        if pd.notna(row.get('analyst_target')):
            upside = ((row['analyst_target'] - row['price']) / row['price']) * 100
            col2.metric("Analyst Target", f"{currency}{row['analyst_target']:.2f}", f"{upside:+.1f}%")
        if pd.notna(row.get('analyst_recommendation')):
            col3.metric("Recommendation", row['analyst_recommendation'])
    
    # Target/Stop prices
    st.markdown("#### Trade Setup")
    col1, col2, col3 = st.columns(3)
    if row.get('target_price'):
        target_pct = ((row['target_price']/row['entry_price'])-1)*100
        col1.metric("Target Price", f"{currency}{row['target_price']:.2f}", f"+{target_pct:.1f}%")
    if row.get('stop_loss'):
        stop_pct = ((row['stop_loss']/row['entry_price'])-1)*100
        col2.metric("Stop Loss", f"{currency}{row['stop_loss']:.2f}", f"{stop_pct:.1f}%")
    if row.get('risk_reward_ratio'):
        col3.metric("Risk/Reward", f"{row['risk_reward_ratio']:.2f}")
    
    # Reasons
    try:
        if 'reasons' in row and pd.notna(row['reasons']):
            reasons_value = row['reasons']
            if isinstance(reasons_value, str) and reasons_value not in ['', '[]']:
                st.markdown("#### Technical Signals")
                reasons = eval(reasons_value)
                for reason in reasons[:5]:
                    st.markdown(f"• {reason}")
            elif isinstance(reasons_value, list) and len(reasons_value) > 0:
                st.markdown("#### Technical Signals")
                for reason in reasons_value[:5]:
                    st.markdown(f"• {reason}")
    except:
        pass
    
    # Fundamental reasons (if available)
    try:
        if has_fundamentals and 'fundamental_reasons' in row and pd.notna(row.get('fundamental_reasons')):
            fund_reasons_value = row['fundamental_reasons']
            if isinstance(fund_reasons_value, str) and fund_reasons_value not in ['', '[]']:
                st.markdown("#### Fundamental Highlights")
                fund_reasons = eval(fund_reasons_value)
                for reason in fund_reasons:
                    st.markdown(f"• {reason}")
            elif isinstance(fund_reasons_value, list) and len(fund_reasons_value) > 0:
                st.markdown("#### Fundamental Highlights")
                for reason in fund_reasons_value:
                    st.markdown(f"• {reason}")
    except:
        pass
    
    # Chart
    st.markdown("#### Technical Chart")
    chart = plot_stock_chart(row['symbol'], days=90)
    if chart:
        st.plotly_chart(chart, use_container_width=True)

def render_intraday_scanner():
    """Render the intraday scanner tab for multiple datasets"""
    st.markdown("### ⚡ Intraday Trading Scanner")
    st.markdown("*RSI Mean Reversion + VWAP Breakout Strategies*")
    
    # Initialize session state for intraday results
    if 'intraday_signals' not in st.session_state:
        st.session_state.intraday_signals = None
    
    # Settings expander (within the tab)
    with st.expander("⚙️ Scanner Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Dataset selection
            dataset_name = st.selectbox(
                "Dataset",
                ["NIFTY_ALL", "NASDAQ100", "NIFTY50", "NIFTYNEXT50", "NIFTYMIDCAP"],
                index=0,
                help="Select which stock universe to scan",
                key="intraday_dataset"
            )
            
            # Interval selection
            interval = st.selectbox(
                "Data Interval",
                ["5m", "15m", "30m", "60m"],
                index=0,
                help="5m = More signals but noisier, 15m/30m = Balanced, 60m = Less noise",
                key="intraday_interval"
            )
            
            # Strategy parameters
            st.markdown("**Strategy Parameters**")
            rsi_period = st.slider("RSI Period", 5, 30, 14)
            rsi_oversold = st.slider("RSI Oversold", 20, 40, 30)
            rsi_overbought = st.slider("RSI Overbought", 60, 80, 70)
        
        with col2:
            vwap_deviation = st.slider(
                "Min VWAP Deviation %",
                0.0, 1.0, 0.1, 0.05,
                help="Minimum distance from VWAP for breakout signals"
            )
            
            volume_multiplier = st.slider(
                "Volume Multiplier",
                1.0, 3.0, 1.3, 0.1,
                help="Volume must be this many times the average"
            )
            
            # Risk/Reward settings
            st.markdown("**Risk Management**")
            mr_stop = st.number_input("MR Stop %", 0.2, 2.0, 0.5, 0.1)
            mr_target = st.number_input("MR Target %", 0.5, 3.0, 1.0, 0.1)
        
        col1, col2 = st.columns(2)
        with col1:
            bo_stop = st.number_input("BO Stop %", 0.3, 2.0, 0.75, 0.05)
            bo_target = st.number_input("BO Target %", 1.0, 5.0, 2.0, 0.25)
        
        with col2:
            # Scan button
            if st.button("🔍 Run Scan", type="primary", use_container_width=True, key="intraday_run_scan"):
                with st.spinner(f"Scanning {dataset_name} at {interval} intervals..."):
                    scanner = IntradayScanner(
                        rsi_period=rsi_period,
                        rsi_oversold=rsi_oversold,
                        rsi_overbought=rsi_overbought,
                        vwap_deviation=vwap_deviation,
                        volume_multiplier=volume_multiplier,
                        mr_stop_pct=mr_stop,
                        mr_target_pct=mr_target,
                        bo_stop_pct=bo_stop,
                        bo_target_pct=bo_target
                    )
                    
                    signals = scanner.scan_dataset(dataset_name=dataset_name, interval=interval, max_workers=15)
                    st.session_state.intraday_signals = signals
                    
                if signals:
                    st.success(f"✅ Found {len(signals)} intraday signals!")
                else:
                    st.warning("No signals found at this time. Try a different interval or wait for market activity.")
                st.rerun()
    
    # Instructions
    with st.expander("📚 How to Use This Scanner", expanded=True):
        st.markdown("""
        **Intraday Scanner - Real-Time Trading Signals**
        
        This scanner finds intraday trading opportunities using technical analysis on multiple timeframes.
        
        **Quick Start:**
        1. **Choose Timeframe** - Select 5m, 15m, 30m, or 60m intervals
        2. **Adjust Parameters** - Set RSI levels and VWAP sensitivity
        3. **Run Scan** - Click "🔍 Scan NASDAQ 100"
        4. **View Signals** - See BUY/SELL signals with entry and targets
        
        **Two Strategies:**
        - 🔄 **Mean Reversion** - Buy oversold (RSI <30), Sell overbought (RSI >70)
        - 🚀 **VWAP Breakout** - Trade breakouts above/below VWAP with volume confirmation
        
        **Signal Quality:**
        - 🟢 **BUY** - Price below VWAP or RSI oversold, rising
        - 🔴 **SELL** - Price above VWAP or RSI overbought, falling
        - ⭐ **HIGH Confidence** - Strong volume and clear pattern
        
        **Trading Tips:**
        - Use 15m or 30m for best balance (not too noisy)
        - Set stop loss 0.5-1% below entry
        - Take profit at 1-2% target
        - Typical holding: 15 mins to 4 hours
        - Trade during market hours (9:30 AM - 4:00 PM ET)
        """)
    
    # Display results
    if st.session_state.intraday_signals:
        signals = st.session_state.intraday_signals
        
        # Summary metrics
        st.subheader("📊 Signal Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        buy_signals = [s for s in signals if s.signal == "BUY"]
        sell_signals = [s for s in signals if s.signal == "SELL"]
        mr_signals = [s for s in signals if s.strategy == "MEAN_REVERSION"]
        bo_signals = [s for s in signals if s.strategy == "VWAP_BREAKOUT"]
        high_conf = [s for s in signals if s.confidence == "HIGH"]
        
        with col1:
            st.metric("Total Signals", len(signals))
        with col2:
            st.metric("📈 BUY", len(buy_signals), delta=None)
        with col3:
            st.metric("📉 SELL", len(sell_signals), delta=None)
        with col4:
            st.metric("⭐ High Confidence", len(high_conf))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔄 Mean Reversion", len(mr_signals))
        with col2:
            st.metric("🚀 VWAP Breakout", len(bo_signals))
        
        st.divider()
        
        # Filter options
        st.subheader("🎯 Trading Signals")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            signal_filter = st.selectbox("Signal", ["All", "BUY", "SELL"], key="intraday_signal_filter")
        with col2:
            strategy_filter = st.selectbox("Strategy", ["All", "MEAN_REVERSION", "VWAP_BREAKOUT"], key="intraday_strategy_filter")
        with col3:
            conf_filter = st.selectbox("Confidence", ["All", "HIGH", "MEDIUM", "LOW"], key="intraday_confidence_filter")
        
        # Filter signals
        filtered = signals
        if signal_filter != "All":
            filtered = [s for s in filtered if s.signal == signal_filter]
        if strategy_filter != "All":
            filtered = [s for s in filtered if s.strategy == strategy_filter]
        if conf_filter != "All":
            filtered = [s for s in filtered if s.confidence == conf_filter]
        
        if not filtered:
            st.info("No signals match the current filters.")
            return
        
        # Convert to DataFrame for display
        signal_data = []
        for s in filtered:
            currency = get_currency_symbol(s.symbol)
            signal_data.append({
                'Symbol': s.symbol,
                'Signal': s.signal,
                'Strategy': s.strategy.replace('_', ' ').title(),
                'Confidence': s.confidence,
                'Price': f"{currency}{s.current_price:.2f}",
                'Entry': f"{currency}{s.entry_price:.2f}",
                'Stop': f"{currency}{s.stop_loss:.2f}",
                'Target': f"{currency}{s.target_price:.2f}",
                'R:R': f"{s.risk_reward:.2f}",
                'RSI': f"{s.rsi:.1f}",
                'VWAP Dist': f"{s.vwap_distance:+.2f}%",
                'Vol Ratio': f"{s.volume_ratio:.1f}x",
                'Trend': s.trend
            })
        
        df_signals = pd.DataFrame(signal_data)
        
        # Style the dataframe
        def highlight_signal(row):
            if row['Signal'] == 'BUY':
                return ['background-color: rgba(40, 167, 69, 0.1)'] * len(row)
            elif row['Signal'] == 'SELL':
                return ['background-color: rgba(220, 53, 69, 0.1)'] * len(row)
            return [''] * len(row)
        
        styled_df = df_signals.style.apply(highlight_signal, axis=1)
        
        # Display with row selection
        event = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Show details when row is selected
        if event.selection and event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_signal = filtered[selected_idx]
            
            st.divider()
            st.subheader(f"📋 {selected_signal.symbol} - {selected_signal.signal} Signal Details")
            
            currency = get_currency_symbol(selected_signal.symbol)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                signal_class = f"{selected_signal.signal.lower()}-signal"
                st.markdown(f"**Signal:** <span class='{signal_class}'>{selected_signal.signal}</span>", 
                           unsafe_allow_html=True)
                st.metric("Strategy", selected_signal.strategy.replace('_', ' ').title())
            
            with col2:
                st.metric("Confidence", selected_signal.confidence)
                st.metric("Current Price", f"{currency}{selected_signal.current_price:.2f}")
            
            with col3:
                st.metric("Entry Price", f"{currency}{selected_signal.entry_price:.2f}")
                stop_pct = abs((selected_signal.stop_loss - selected_signal.entry_price) / selected_signal.entry_price * 100)
                st.metric("Stop Loss", f"{currency}{selected_signal.stop_loss:.2f}", f"-{stop_pct:.2f}%")
            
            with col4:
                target_pct = abs((selected_signal.target_price - selected_signal.entry_price) / selected_signal.entry_price * 100)
                st.metric("Target Price", f"{currency}{selected_signal.target_price:.2f}", f"+{target_pct:.2f}%")
                st.metric("Risk/Reward", f"{selected_signal.risk_reward:.2f}:1")
            
            # Indicators
            st.markdown("#### 📊 Technical Indicators")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("RSI", f"{selected_signal.rsi:.1f}")
            with col2:
                st.metric("VWAP", f"{currency}{selected_signal.vwap:.2f}")
            with col3:
                st.metric("VWAP Distance", f"{selected_signal.vwap_distance:+.2f}%")
            with col4:
                st.metric("Volume Ratio", f"{selected_signal.volume_ratio:.1f}x avg")
            
            st.metric("Trend", selected_signal.trend)
            
            # Reasons
            if selected_signal.reasons:
                st.markdown("#### ✅ Signal Reasons")
                for reason in selected_signal.reasons:
                    st.markdown(f"• {reason}")
            
            # Timestamp
            st.caption(f"Generated: {selected_signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Export option
        st.divider()
        if st.button("💾 Export Signals to CSV", key="export_intraday_csv"):
            export_data = []
            for s in signals:
                export_data.append({
                    'Symbol': s.symbol,
                    'Signal': s.signal,
                    'Strategy': s.strategy,
                    'Confidence': s.confidence,
                    'Current_Price': s.current_price,
                    'Entry': s.entry_price,
                    'Stop_Loss': s.stop_loss,
                    'Target': s.target_price,
                    'Risk_Reward': s.risk_reward,
                    'RSI': s.rsi,
                    'VWAP': s.vwap,
                    'VWAP_Distance_%': s.vwap_distance,
                    'Volume_Ratio': s.volume_ratio,
                    'Trend': s.trend,
                    'Reasons': ' | '.join(s.reasons),
                    'Timestamp': s.timestamp.isoformat()
                })
            
            export_df = pd.DataFrame(export_data)
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"intraday_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    else:
        # Show instructions
        st.info("👈 Click **Scan NASDAQ 100** in the sidebar to find intraday trading signals")
        
        st.markdown("### 📚 How It Works")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            #### 🔄 Mean Reversion Strategy
            - Identifies **oversold** (RSI < 30) or **overbought** (RSI > 70) conditions
            - Looks for reversal signals (RSI turning)
            - Best for **ranging/choppy markets**
            - Quick targets: **0.5-1%** moves
            - Higher win rate but smaller gains
            """)
        
        with col2:
            st.markdown("""
            #### 🚀 VWAP Breakout Strategy
            - Detects price breaking **above/below VWAP**
            - Requires volume confirmation
            - Best for **trending markets**
            - Larger targets: **1-2%** moves
            - Lower win rate but bigger potential
            """)
        
        st.markdown("### ⚙️ Strategy Parameters")
        st.markdown("""
        - **Interval**: 5m (frequent signals), 15m (balanced), 30m/60m (less noise)
        - **RSI**: 14-period default, overbought >70, oversold <30
        - **VWAP**: Minimum 0.1% distance for valid breakout
        - **Volume**: Must be 1.3x average volume
        - **Risk/Reward**: 2:1 ratio typical
        """)
        
        st.warning("⚠️ **Trading Hours**: Signals are more reliable during market hours (9:30 AM - 4:00 PM ET)")

# Main App
def main():
    # Load cached results on startup if not already in session
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None:
        cached_results, cached_metadata = load_cached_scan_results()
        if cached_results is not None:
            st.session_state.scan_results = cached_results
            st.session_state.scan_metadata = cached_metadata
    
    # Header
    st.markdown('<p class="main-header">📈 Stock Scanner - Swing & Intraday Trading</p>', 
               unsafe_allow_html=True)
    st.markdown("*Technical Analysis for Swing Trading (2-30 days) & Intraday Signals*")
    
    # Create tabs for different scanners
    tab1, tab2, tab3 = st.tabs([
        "📊 Stock Scanner (Swing Trading)",
        "⚡ Intraday Scanner (Live)",
        "🌅 Pre-Market Watchlist"
    ])
    
    with tab1:
        render_stock_scanner()
    
    with tab2:
        render_intraday_scanner()
    
    with tab3:
        render_premarket_scanner()

def render_stock_scanner():
    
    # Settings expander (within the tab)
    with st.expander("⚙️ Scan Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Analysis type
            include_fundamentals = st.checkbox(
                "Include Fundamental Analysis",
                value=True,
                help="Add P/E, growth, profitability, debt metrics (slower but more comprehensive)"
            )
            
            # Dataset selection
            dataset_name = st.selectbox(
                "Dataset",
                ["NIFTY_ALL", "COMBINED", "SP500", "NASDAQ100", "NIFTY50", "NIFTYNEXT50", "NIFTYMIDCAP", "ALL"],
                help="Select which stock universe to scan",
                key="stock_dataset"
            )
            
            # Sector filter
            sectors = get_sectors(dataset_name)
            sector_options = ["All"] + sectors
            sector_filter = st.selectbox(
                "Sector",
                sector_options,
                help="Filter by specific sector",
                key="stock_sector_filter"
            )
        
        with col2:
            # Signal filter
            signal_filter = st.selectbox(
                "Signal Type",
                ["All", "BUY", "SELL", "HOLD"],
                help="Filter by trading signal",
                key="stock_signal_filter"
            )
            
            # Score threshold
            min_score = st.slider(
                "Minimum Score",
                min_value=0,
                max_value=100,
                value=30,
                step=5,
                help="Minimum technical score (0-100). Lower = more results"
            )
            
            # Max stocks
            max_stocks = st.number_input(
                "Max Stocks to Scan",
                min_value=10,
                max_value=500,
                value=200,
                step=10,
                help="Limit number of stocks (avoid rate limits)"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Scan button
            if st.button("🔍 Run Scan", type="primary", use_container_width=True, key="stock_run_scan"):
                # Get dataset info
                collector = get_dataset_collector()
                dataset_df = collector.load_dataset(dataset_name)
                total_in_dataset = len(dataset_df) if dataset_df is not None else 0
                
                results = scan_stocks(dataset_name, sector_filter, signal_filter, 
                                    min_score, max_stocks, include_fundamentals)
                st.session_state.scan_results = results
                st.session_state.selected_stock = None
                st.session_state.include_fundamentals = include_fundamentals
                # Update metadata
                st.session_state.scan_metadata = {
                    'timestamp': datetime.now().isoformat(),
                    'scan_params': {
                        'dataset': dataset_name,
                        'sector': sector_filter,
                        'signal': signal_filter,
                        'min_score': min_score,
                        'max_stocks': max_stocks,
                        'include_fundamentals': include_fundamentals,
                        'total_in_dataset': total_in_dataset,
                        'stocks_with_data': len(results)
                    },
                    'num_results': len(results)
                }
                
                failed = total_in_dataset - len(results)
                st.success(f"✅ Scan complete! {len(results)}/{total_in_dataset} stocks with data ({failed} failed/no data)")
                st.rerun()
        
        with col2:
            # Clear cache button
            if st.button("🗑️ Clear Cache", use_container_width=True, key="clear_cache_button"):
                cache_file = Path(__file__).parent / 'data' / 'cache' / 'scan_results_cache.parquet'
                metadata_file = Path(__file__).parent / 'data' / 'cache' / 'scan_results_metadata.json'
                if cache_file.exists():
                    cache_file.unlink()
                if metadata_file.exists():
                    metadata_file.unlink()
                st.session_state.scan_results = None
                st.session_state.scan_metadata = None
                st.success("Scan cache cleared!")
                st.rerun()
        
        # Show cached scan info if available
        if 'scan_metadata' in st.session_state:
            metadata = st.session_state.scan_metadata
            scan_time = datetime.fromisoformat(metadata['timestamp'])
            time_ago = datetime.now() - scan_time
            
            if time_ago < timedelta(hours=1):
                time_str = f"{int(time_ago.total_seconds() / 60)} min ago"
            elif time_ago < timedelta(days=1):
                time_str = f"{int(time_ago.total_seconds() / 3600)} hrs ago"
            else:
                time_str = f"{time_ago.days} days ago"
            
            scan_params = metadata.get('scan_params', {})
            total_in_dataset = scan_params.get('total_in_dataset', 'N/A')
            stocks_with_data = scan_params.get('stocks_with_data', metadata['num_results'])
            
            st.info(f"""📦 **Cached Results** — {time_str}
**Dataset:** {scan_params.get('dataset', 'N/A')} ({total_in_dataset} stocks) | **With Data:** {stocks_with_data} | **After Filters:** {metadata['num_results']}""")
    
    # Instructions
    with st.expander("📚 How to Use This Scanner", expanded=True):
        st.markdown("""
        **Stock Scanner - Swing Trading (2-30 Days)**
        
        This scanner identifies stocks with strong technical signals for swing trading opportunities.
        
        **Quick Start:**
        1. **Adjust Settings** (top) - Choose your dataset, filters, and scoring preferences
        2. **Run Scan** - Click the "🔍 Run Scan" button
        3. **Review Results** - See stocks ranked by score with buy/sell signals
        4. **Click Stock** - View detailed charts and analysis
        
        **What to Look For:**
        - 🟢 **BUY signals** - Stocks with bullish momentum (Green)
        - 🔴 **SELL signals** - Stocks with bearish pressure (Red)
        - ⭐ **HIGH Confidence** - Higher probability trades
        - 📈 **Trending Up** - Price above key moving averages
        
        **Pro Tips:**
        - Start with HIGH confidence signals only
        - Check the entry/target/stop loss prices
        - Review 2-3 day chart patterns before trading
        - Typical holding period: 2-30 days
        """)
    
    # Main content
    if st.session_state.scan_results is not None:
        results = st.session_state.scan_results
        
        if len(results) == 0:
            st.warning("No stocks found matching your criteria. Try adjusting the filters.")
            return
        
        # Summary metrics
        st.subheader("📊 Scan Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Stocks", len(results))
        with col2:
            buy_count = len(results[results['signal'] == 'BUY'])
            st.metric("Buy Signals", buy_count)
        with col3:
            avg_score = results['technical_score'].mean()
            st.metric("Avg Score", f"{avg_score:.1f}")
        with col4:
            high_conf = len(results[results['confidence'] == 'HIGH'])
            st.metric("High Confidence", high_conf)
        
        st.divider()
        
        # Results table
        st.subheader("🎯 Top Picks")
        
        # Check if fundamentals are included
        has_fundamentals = 'fundamental_score' in results.columns
        
        # Sort options
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_options = ["technical_score", "price", "target_price", "trend_score", 
                          "momentum_score", "volatility_score"]
            if has_fundamentals:
                sort_options = ["composite_score", "technical_score", "fundamental_score", 
                              "price", "valuation_score", "growth_score", "profitability_score"]
            sort_by = st.selectbox(
                "Sort by",
                sort_options,
                index=0,
                key="stock_sort_by"
            )
        with col2:
            ascending = st.checkbox("Ascending", value=False)
        
        # Sort and display
        sorted_results = results.sort_values(by=sort_by, ascending=ascending).reset_index(drop=True)
        
        # Display table with clickable rows
        base_columns = ['symbol', 'price', 'technical_score', 'signal', 'confidence']
        if has_fundamentals:
            display_columns = base_columns + ['fundamental_score', 'composite_score', 'pe_ratio', 'earnings_growth']
        else:
            display_columns = base_columns + ['entry_price', 'target_price', 'stop_loss']
        
        # Filter out columns that don't exist
        display_columns = [col for col in display_columns if col in sorted_results.columns]
        display_df = sorted_results[display_columns].copy()
        
        # Format columns
        display_df['price'] = display_df.apply(lambda row: f"{get_currency_symbol(row['symbol'])}{sorted_results.loc[row.name, 'price']:.2f}", axis=1)
        display_df['technical_score'] = display_df['technical_score'].apply(lambda x: f"{x:.1f}")
        if 'fundamental_score' in display_df.columns:
            display_df['fundamental_score'] = display_df['fundamental_score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        if 'composite_score' in display_df.columns:
            display_df['composite_score'] = display_df['composite_score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        if 'pe_ratio' in display_df.columns:
            display_df['pe_ratio'] = display_df['pe_ratio'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        if 'earnings_growth' in display_df.columns:
            display_df['earnings_growth'] = display_df['earnings_growth'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        if 'entry_price' in display_df.columns:
            display_df['entry_price'] = display_df.apply(lambda row: f"{get_currency_symbol(row['symbol'])}{sorted_results.loc[row.name, 'entry_price']:.2f}" if pd.notna(sorted_results.loc[row.name, 'entry_price']) else "N/A", axis=1)
        if 'target_price' in display_df.columns:
            display_df['target_price'] = display_df.apply(lambda row: f"{get_currency_symbol(row['symbol'])}{sorted_results.loc[row.name, 'target_price']:.2f}" if pd.notna(sorted_results.loc[row.name, 'target_price']) else "N/A", axis=1)
        if 'stop_loss' in display_df.columns:
            display_df['stop_loss'] = display_df.apply(lambda row: f"{get_currency_symbol(row['symbol'])}{sorted_results.loc[row.name, 'stop_loss']:.2f}" if pd.notna(sorted_results.loc[row.name, 'stop_loss']) else "N/A", axis=1)
        
        # Apply color styling
        def style_dataframe(df):
            styled = df.style
            # Color score columns
            score_cols = ['technical_score', 'fundamental_score', 'composite_score']
            for col in score_cols:
                if col in df.columns:
                    styled = styled.map(color_score, subset=[col])
            # Color signal
            if 'signal' in df.columns:
                styled = styled.map(color_signal, subset=['signal'])
            # Color confidence
            if 'confidence' in df.columns:
                styled = styled.map(color_confidence, subset=['confidence'])
            return styled
        
        # Display styled dataframe with selection
        event = st.dataframe(
            style_dataframe(display_df),
            use_container_width=True,
            height=400,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle row selection
        if event.selection and event.selection.rows:
            st.session_state.selected_row_index = event.selection.rows[0]
        
        st.caption("💡 Click on a row to view detailed analysis")
        
        # Download button
        csv = sorted_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name=f"stock_scan_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.divider()
        
        # Stock detail view
        st.subheader("🔍 Stock Details")
        
        # Use selected row from table or default to first stock
        selected_idx = st.session_state.selected_row_index if st.session_state.selected_row_index is not None else 0
        
        if selected_idx < len(sorted_results):
            stock_row = sorted_results.iloc[selected_idx]
            st.markdown(f"**Showing details for: {stock_row['symbol']}**")
            display_stock_detail(stock_row)
        else:
            st.info("Click on a stock in the table above to view detailed analysis.")
    
    else:
        # Welcome screen
        st.info("👈 Configure your scan settings and click **Run Scan** to get started!")
        
        st.markdown("### 🚀 Features")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ✅ **Technical Analysis**
            - RSI, MACD, Moving Averages
            - Bollinger Bands, ATR
            - Volume analysis
            
            ✅ **Fundamental Analysis**
            - Valuation (P/E, PEG, P/B)
            - Growth (earnings, revenue)
            - Profitability (margins, ROE)
            - Financial Health (debt, FCF)
            
            ✅ **Smart Filtering**
            - Filter by sector
            - Minimum score threshold
            - Signal type (BUY/SELL/HOLD)
            """)
        
        with col2:
            st.markdown("""
            ✅ **Interactive Charts**
            - Candlestick charts
            - Technical indicators overlay
            - RSI and volume subplots
            
            ✅ **Performance**
            - Caching system (24h/1h)
            - Parallel processing
            - Export to CSV
            """)
        
        st.markdown("### 📚 Quick Start")
        st.markdown("""
        1. **Select Dataset**: Choose S&P 500, NASDAQ 100, or Combined
        2. **Apply Filters**: Sector, signal type, minimum score
        3. **Run Scan**: Click the scan button (takes 1-3 minutes)
        4. **Explore Results**: Sort, filter, view charts
        5. **Download**: Export results as CSV
        """)
        
        st.warning("⚠️ **Note**: First scan may take longer. Subsequent scans use cached data for 20-100x speedup!")


def render_premarket_scanner():
    """Render the pre-market watchlist scanner tab"""
    st.header("🌅 Pre-Market Watchlist")
    st.markdown("**Prepare your intraday watchlist BEFORE market opens at 9:30 AM ET**")
    
    # Settings expander (within the tab)
    with st.expander("⚙️ Scan Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Dataset selection
            dataset_name = st.selectbox(
                "Dataset",
                ["NIFTY_ALL", "NASDAQ100", "SP500", "COMBINED", "NIFTY50", "NIFTYNEXT50", "NIFTYMIDCAP"],
                help="Choose which stocks to scan for pre-market watchlist",
                key="premarket_dataset"
            )
            
            # Filters
            st.markdown("**Price & Volume**")
            
            min_price = st.number_input(
                "Min Price ($)",
                min_value=1.0,
                max_value=100.0,
                value=5.0,
                step=1.0,
                help="Minimum stock price (avoid penny stocks)"
            )
            
            max_price = st.number_input(
                "Max Price ($)",
                min_value=100.0,
                max_value=1000.0,
                value=500.0,
                step=50.0,
                help="Maximum stock price"
            )
        
        with col2:
            min_volume = st.number_input(
                "Min Volume",
                min_value=100000,
                max_value=5000000,
                value=500000,
                step=100000,
                format="%d",
                help="Minimum daily average volume"
            )
            
            min_atr_pct = st.slider(
                "Min ATR %",
                0.5, 5.0, 1.0, 0.1,
                help="Minimum Average True Range % - higher = more volatile/active"
            )
        
        # Scan button
        if st.button("🔍 Scan for Pre-Market Watchlist", type="primary", use_container_width=True, key="premarket_run_scan"):
            with st.spinner(f"Scanning {dataset_name} for pre-market watchlist..."):
                scanner = PreMarketScanner(
                    min_price=min_price,
                    max_price=max_price,
                    min_volume=int(min_volume),
                    min_atr_pct=min_atr_pct
                )
                
                # Scan the selected dataset
                signals = scanner.scan_dataset(dataset_name=dataset_name, max_workers=15)
                
                st.session_state.premarket_signals = signals
                st.session_state.premarket_timestamp = datetime.now()
    
    # Display watchlist size
    if 'premarket_signals' in st.session_state and st.session_state.premarket_signals:
        st.metric(
            "📊 Watchlist Size",
            len(st.session_state.premarket_signals),
            help="Number of stocks on watchlist"
        )
    
    # Instructions
    with st.expander("📚 How to Use This Scanner", expanded=True):
        st.markdown("""
        **Pre-Market Watchlist - Daily Analysis for Intraday Setup**
        
        Run this scanner BEFORE market opens to identify high-probability intraday trading setups.
        
        **Quick Start:**
        1. **Adjust Filters** (top) - Price range, volume, volatility preferences
        2. **Run Scan** - Click "🔍 Scan for Pre-Market Watchlist"
        3. **Review Setups** - See 4 types of technical patterns
        4. **Export List** - Save CSV for your trading day
        
        **4 Setup Types:**
        - 📈 **BREAKOUT** - Price near recent highs, ready to break up
        - 🔄 **REVERSAL** - Oversold in uptrend, bounce expected
        - 🚀 **MOMENTUM** - Price pulled back to moving average, resuming up
        - 📦 **RANGE_BOUND** - Consolidating in tight range, waiting for direction
        
        **What Each Column Means:**
        - **Key Level** - Support/resistance to watch
        - **Stop** - Where to cut losses (typically 0.5-1% below)
        - **Target** - Profit target (typically 1-3% above)
        - **ATR %** - Volatility indicator (higher = more active)
        - **RSI** - Momentum (30-70 range is normal)
        
        **Best Practices:**
        - Run 30-60 min BEFORE market open
        - Focus on HIGH confidence stocks
        - Export watchlist and monitor gaps at open
        - Set alerts on key support/resistance levels
        - Use these as starting point, confirm with live price action
        """)
    
    # Display results
    if 'premarket_signals' not in st.session_state or not st.session_state.premarket_signals:
        # Instructions when no signals
        st.info("👆 Click the scan button above to generate your pre-market watchlist")
        
        st.markdown("### 📋 What This Scanner Does")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🎯 Setup Types**
            - **BREAKOUT**: Near resistance/support, ready to break
            - **REVERSAL**: Oversold/overbought in trend, ready to reverse
            - **MOMENTUM**: Pullback to support in trend, ready to continue
            - **RANGE_BOUND**: In tight range, good for scalping
            """)
        
        with col2:
            st.markdown("""
            **📊 Key Features**
            - Uses daily data (works pre-market)
            - Identifies high-probability setups
            - Provides key levels (support/resistance)
            - Suggests what to watch during the day
            - Filters by volatility (ATR) and volume
            """)
        
        st.markdown("### 💡 How to Use")
        st.markdown("""
        1. **Run Before Market Open**: Scan stocks using yesterday's close data
        2. **Review Watchlist**: See setup types and key levels
        3. **Monitor During Day**: Watch for triggers mentioned in "Watch For" column
        4. **Execute Trades**: Enter based on intraday confirmation
        """)
        
        st.warning("""
        ⚠️ **Important**: This is a WATCHLIST, not a trade signal. 
        Wait for intraday confirmation before entering trades.
        Use the "Intraday Scanner" tab during market hours for real-time signals.
        """)
        
    else:
        # Display scan timestamp
        timestamp = st.session_state.premarket_timestamp
        st.caption(f"Last scan: {timestamp.strftime('%Y-%m-%d %I:%M:%S %p')}")
        
        signals = st.session_state.premarket_signals
        
        # Summary metrics
        st.markdown("### 📊 Watchlist Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Stocks", len(signals))
        
        with col2:
            long_count = len([s for s in signals if s.direction == "LONG"])
            st.metric("Long Setups", long_count)
        
        with col3:
            short_count = len([s for s in signals if s.direction == "SHORT"])
            st.metric("Short Setups", short_count)
        
        with col4:
            high_conf = len([s for s in signals if s.confidence == "HIGH"])
            st.metric("High Confidence", high_conf)
        
        # Breakdown by setup type
        st.markdown("### 🎯 Setup Type Breakdown")
        
        setup_counts = {}
        for signal in signals:
            setup_counts[signal.setup_type] = setup_counts.get(signal.setup_type, 0) + 1
        
        cols = st.columns(len(setup_counts))
        for i, (setup_type, count) in enumerate(setup_counts.items()):
            with cols[i]:
                st.metric(setup_type.replace("_", " ").title(), count)
        
        st.divider()
        
        # Filters
        st.markdown("### 🔍 Filter Watchlist")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            direction_filter = st.selectbox(
                "Direction",
                ["All", "LONG", "SHORT", "BOTH"],
                key="premarket_direction_filter"
            )
        
        with col2:
            setup_filter = st.selectbox(
                "Setup Type",
                ["All"] + list(setup_counts.keys()),
                key="premarket_setup_filter"
            )
        
        with col3:
            confidence_filter = st.selectbox(
                "Confidence",
                ["All", "HIGH", "MEDIUM", "LOW"],
                key="premarket_confidence_filter"
            )
        
        # Apply filters
        filtered_signals = signals
        if direction_filter != "All":
            filtered_signals = [s for s in filtered_signals if s.direction == direction_filter]
        if setup_filter != "All":
            filtered_signals = [s for s in filtered_signals if s.setup_type == setup_filter]
        if confidence_filter != "All":
            filtered_signals = [s for s in filtered_signals if s.confidence == confidence_filter]
        
        st.caption(f"Showing {len(filtered_signals)} of {len(signals)} stocks")
        
        # Convert to DataFrame for display
        df_data = []
        for signal in filtered_signals:
            currency = get_currency_symbol(signal.symbol)
            df_data.append({
                "Symbol": signal.symbol,
                "Setup": signal.setup_type.replace("_", " ").title(),
                "Direction": signal.direction,
                "Confidence": signal.confidence,
                "Price": f"{currency}{signal.current_price:.2f}",
                "Key Level": f"{currency}{signal.key_level:.2f}",
                "Stop": f"{currency}{signal.stop_level:.2f}",
                "Target": f"{currency}{signal.target_level:.2f}",
                "ATR %": f"{signal.atr / signal.current_price * 100:.2f}%",
                "RSI": f"{signal.rsi:.1f}",
                "Volume Ratio": f"{signal.volume_ratio:.1f}x",
                "Trend": signal.trend
            })
        
        df_display = pd.DataFrame(df_data)
        
        # Display table with selection
        st.markdown("### 📋 Watchlist")
        
        # Color code by direction
        def color_direction(row):
            if row['Direction'] == 'LONG':
                return ['background-color: #1e4620; color: white'] * len(row)
            elif row['Direction'] == 'SHORT':
                return ['background-color: #4a1a1a; color: white'] * len(row)
            else:
                return ['background-color: #1a1a2e; color: white'] * len(row)
        
        styled_df = df_display.style.apply(color_direction, axis=1)
        
        # Make table interactive
        event = st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Show details for selected row
        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_signal = filtered_signals[selected_idx]
            
            st.markdown("---")
            st.markdown(f"### 📌 {selected_signal.symbol} - Detailed View")
            
            currency = get_currency_symbol(selected_signal.symbol)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🎯 Setup Details**")
                st.write(f"**Type**: {selected_signal.setup_type.replace('_', ' ').title()}")
                st.write(f"**Direction**: {selected_signal.direction}")
                st.write(f"**Confidence**: {selected_signal.confidence}")
                st.write(f"**Trend**: {selected_signal.trend}")
            
            with col2:
                st.markdown("**💰 Price Levels**")
                st.write(f"**Current**: {currency}{selected_signal.current_price:.2f}")
                st.write(f"**Key Level**: {currency}{selected_signal.key_level:.2f}")
                st.write(f"**Stop Loss**: {currency}{selected_signal.stop_level:.2f}")
                st.write(f"**Target**: {currency}{selected_signal.target_level:.2f}")
            
            with col3:
                st.markdown("**📊 Indicators**")
                st.write(f"**RSI**: {selected_signal.rsi:.1f}")
                st.write(f"**ATR**: {currency}{selected_signal.atr:.2f} ({selected_signal.atr / selected_signal.current_price * 100:.2f}%)")
                st.write(f"**Volume**: {selected_signal.volume_ratio:.1f}x avg")
            
            st.markdown("**📝 Setup Reasons**")
            for reason in selected_signal.reasons:
                st.write(f"• {reason}")
            
            st.markdown("**👀 Watch For (During Trading Day)**")
            for item in selected_signal.watch_for:
                st.success(f"✓ {item}")
        
        # Export functionality
        st.markdown("---")
        if st.button("📥 Export Watchlist to CSV", key="export_premarket_csv"):
            # Create detailed CSV
            csv_data = []
            for signal in filtered_signals:
                csv_data.append({
                    "Symbol": signal.symbol,
                    "Setup_Type": signal.setup_type,
                    "Direction": signal.direction,
                    "Confidence": signal.confidence,
                    "Current_Price": signal.current_price,
                    "Key_Level": signal.key_level,
                    "Stop_Loss": signal.stop_level,
                    "Target": signal.target_level,
                    "ATR": signal.atr,
                    "ATR_Pct": signal.atr / signal.current_price * 100,
                    "RSI": signal.rsi,
                    "Volume_Ratio": signal.volume_ratio,
                    "Trend": signal.trend,
                    "Reasons": " | ".join(signal.reasons),
                    "Watch_For": " | ".join(signal.watch_for),
                    "Timestamp": signal.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            csv_df = pd.DataFrame(csv_data)
            csv = csv_df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"premarket_watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
