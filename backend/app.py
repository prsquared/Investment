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

# Page configuration
st.set_page_config(
    page_title="Stock Scanner - Swing Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
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

def color_score(val):
    """Apply color to score values."""
    try:
        # Extract numeric value from formatted string
        num_val = float(val.replace('$', '').replace('%', '').replace(',', ''))
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
    except FileNotFoundError:
        # Datasets don't exist, fetch them
        collector.fetch_all_datasets()
        datasets['SP500'] = collector.load_dataset('SP500')
        datasets['NASDAQ100'] = collector.load_dataset('NASDAQ100')
        datasets['COMBINED'] = collector.load_dataset('COMBINED')
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
    st.markdown(f"### 📊 {row['symbol']} - ${row['price']:.2f}")
    
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
            st.metric("Entry Price", f"${row['entry_price']:.2f}")
    
    with col3:
        if has_fundamentals:
            st.metric("Composite Score", f"{row['composite_score']:.1f}/100",
                     help="60% Technical + 40% Fundamental")
        else:
            target_pct = ((row['target_price']/row['entry_price'])-1)*100
            st.metric("Target Price", f"${row['target_price']:.2f}", 
                     f"+{target_pct:.1f}%")
    
    with col4:
        if has_fundamentals and row.get('entry_price'):
            st.metric("Entry Price", f"${row['entry_price']:.2f}")
        else:
            stop_pct = ((row['stop_loss']/row['entry_price'])-1)*100
            st.metric("Stop Loss", f"${row['stop_loss']:.2f}",
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
            col2.metric("Analyst Target", f"${row['analyst_target']:.2f}", f"{upside:+.1f}%")
        if pd.notna(row.get('analyst_recommendation')):
            col3.metric("Recommendation", row['analyst_recommendation'])
    
    # Target/Stop prices
    st.markdown("#### Trade Setup")
    col1, col2, col3 = st.columns(3)
    if row.get('target_price'):
        target_pct = ((row['target_price']/row['entry_price'])-1)*100
        col1.metric("Target Price", f"${row['target_price']:.2f}", f"+{target_pct:.1f}%")
    if row.get('stop_loss'):
        stop_pct = ((row['stop_loss']/row['entry_price'])-1)*100
        col2.metric("Stop Loss", f"${row['stop_loss']:.2f}", f"{stop_pct:.1f}%")
    if row.get('risk_reward_ratio'):
        col3.metric("Risk/Reward", f"{row['risk_reward_ratio']:.2f}")
    
    # Reasons
    if 'reasons' in row and row['reasons']:
        st.markdown("#### Technical Signals")
        reasons = row['reasons'] if isinstance(row['reasons'], list) else eval(row['reasons'])
        for reason in reasons[:5]:
            st.markdown(f"• {reason}")
    
    # Fundamental reasons (if available)
    if has_fundamentals and 'fundamental_reasons' in row and row['fundamental_reasons']:
        st.markdown("#### Fundamental Highlights")
        fund_reasons = row['fundamental_reasons'] if isinstance(row['fundamental_reasons'], list) else eval(row['fundamental_reasons'])
        for reason in fund_reasons:
            st.markdown(f"• {reason}")
    
    # Chart
    st.markdown("#### Technical Chart")
    chart = plot_stock_chart(row['symbol'], days=90)
    if chart:
        st.plotly_chart(chart, use_container_width=True)

# Main App
def main():
    # Load cached results on startup if not already in session
    if 'scan_results' not in st.session_state or st.session_state.scan_results is None:
        cached_results, cached_metadata = load_cached_scan_results()
        if cached_results is not None:
            st.session_state.scan_results = cached_results
            st.session_state.scan_metadata = cached_metadata
    
    # Header
    st.markdown('<p class="main-header">📈 Stock Scanner - Swing Trading</p>', 
               unsafe_allow_html=True)
    st.markdown("*Technical Analysis for 2-30 Day Hold Periods*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Scan Settings")
        
        # Analysis type
        include_fundamentals = st.checkbox(
            "Include Fundamental Analysis",
            value=False,
            help="Add P/E, growth, profitability, debt metrics (slower but more comprehensive)"
        )
        
        st.divider()
        
        # Dataset selection
        dataset_name = st.selectbox(
            "Dataset",
            ["COMBINED", "SP500", "NASDAQ100"],
            help="Select which stock universe to scan"
        )
        
        # Sector filter
        sectors = get_sectors(dataset_name)
        sector_options = ["All"] + sectors
        sector_filter = st.selectbox(
            "Sector",
            sector_options,
            help="Filter by specific sector"
        )
        
        # Signal filter
        signal_filter = st.selectbox(
            "Signal Type",
            ["All", "BUY", "SELL", "HOLD"],
            help="Filter by trading signal"
        )
        
        # Score threshold
        min_score = st.slider(
            "Minimum Score",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
            help="Minimum technical score (0-100)"
        )
        
        # Max stocks
        max_stocks = st.number_input(
            "Max Stocks to Scan",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="Limit number of stocks (avoid rate limits)"
        )
        
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
            
            st.info(f"""📦 **Cached Results**
            
**Dataset:** {scan_params.get('dataset', 'N/A')} ({total_in_dataset} total stocks)  
**With Data:** {stocks_with_data} stocks  
**After Filters:** {metadata['num_results']} stocks  
**Scanned:** {time_str}""")
        
        # Scan button
        if st.button("🔍 Run Scan", type="primary", use_container_width=True):
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
        
        st.divider()
        
        # Cache management
        st.subheader("💾 Cache")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Data Cache", use_container_width=True):
                fetcher = DataFetcher()
                fetcher.clear_cache()
                st.success("Data cache cleared!")
        with col2:
            if st.button("Clear Scan Cache", use_container_width=True):
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
        
        st.divider()
        st.caption("📚 Data Source: Yahoo Finance")
        st.caption("⚠️ Not Financial Advice")
    
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
                index=0
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
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:.2f}")
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
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        if 'target_price' in display_df.columns:
            display_df['target_price'] = display_df['target_price'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        if 'stop_loss' in display_df.columns:
            display_df['stop_loss'] = display_df['stop_loss'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
        
        # Apply color styling
        def style_dataframe(df):
            styled = df.style
            # Color score columns
            score_cols = ['technical_score', 'fundamental_score', 'composite_score']
            for col in score_cols:
                if col in df.columns:
                    styled = styled.applymap(color_score, subset=[col])
            # Color signal
            if 'signal' in df.columns:
                styled = styled.applymap(color_signal, subset=['signal'])
            # Color confidence
            if 'confidence' in df.columns:
                styled = styled.applymap(color_confidence, subset=['confidence'])
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

if __name__ == "__main__":
    main()
