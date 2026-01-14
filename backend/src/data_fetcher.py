"""
Data fetcher for stock market data using yfinance.
"""
from typing import Optional, List
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from loguru import logger
import time
import json
from pathlib import Path
import hashlib

try:
    from .config import get_config
except ImportError:
    from config import get_config


class DataFetcher:
    """Fetch stock data from Yahoo Finance with caching support."""

    def __init__(self, cache_dir: str = "data/cache", use_cache: bool = True):
        """
        Initialize DataFetcher.
        
        Args:
            cache_dir: Directory to store cache files
            use_cache: Whether to use caching (default: True)
        """
        self.config = get_config().data_source
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        # Cache expiration times (in hours)
        self.historical_cache_hours = 24  # Historical data cached for 24 hours
        self.current_price_cache_hours = 1  # Current price cached for 1 hour
        
        logger.info(f"DataFetcher initialized (cache: {'enabled' if use_cache else 'disabled'})")

    def _get_cache_path(self, cache_type: str, symbol: str, **kwargs) -> Path:
        """Generate cache file path."""
        cache_key = f"{symbol}_{cache_type}"
        if kwargs:
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
            cache_key = f"{cache_key}_{params_str}"
        if len(cache_key) > 100:
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{cache_key}.parquet"

    def _is_cache_valid(self, cache_path: Path, max_age_hours: float) -> bool:
        """Check if cache file is valid."""
        if not cache_path.exists():
            return False
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        if age.total_seconds() / 3600 > max_age_hours:
            return False
        return True

    def _save_to_cache(self, cache_path: Path, data: pd.DataFrame):
        """Save DataFrame to cache."""
        try:
            data.to_parquet(cache_path, index=True)
            logger.debug(f"Cached: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    def _load_from_cache(self, cache_path: Path) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache."""
        try:
            df = pd.read_parquet(cache_path)
            logger.debug(f"Cache hit: {cache_path.name}")
            return df
        except Exception as e:
            return None

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache files."""
        if symbol:
            pattern = f"{symbol.upper()}_*.parquet"
            files = list(self.cache_dir.glob(pattern))
        else:
            files = list(self.cache_dir.glob("*.parquet"))
        for file in files:
            file.unlink()
        logger.info(f"Cleared cache: {len(files)} files")

    def fetch_historical_data(
        self,
        symbol: str,
        days: int = 365,
        interval: str = '1d',
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data for a symbol with caching.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            days: Number of days of historical data
            interval: Data interval ('1d', '1h', etc.)
            force_refresh: Force refresh from API (ignore cache)

        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index is datetime
        """
        symbol = symbol.upper()

        # Check cache first
        if self.use_cache and not force_refresh:
            cache_path = self._get_cache_path('historical', symbol, days=days, interval=interval)
            if self._is_cache_valid(cache_path, self.historical_cache_hours):
                df = self._load_from_cache(cache_path)
                if df is not None:
                    logger.info(f"Using cached data for {symbol} ({len(df)} records)")
                    return df

        try:
            # Calculate date range
            # Account for weekends and holidays: ~252 trading days per year
            # Request 1.5x calendar days to ensure we get enough trading days
            calendar_days = int(days * 1.5)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=calendar_days)

            logger.info(f"Fetching {days} trading days of data for {symbol}")

            # Fetch data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True  # Adjust for splits and dividends
            )

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Standardize column names
            df.columns = df.columns.str.lower()

            # Select and rename columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]

            logger.info(f"Fetched {len(df)} records for {symbol}")

            # Save to cache
            if self.use_cache:
                cache_path = self._get_cache_path('historical', symbol, days=days, interval=interval)
                self._save_to_cache(cache_path, df)

            # Rate limiting
            time.sleep(self.config.api_call_delay)

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None

    def fetch_current_price(self, symbol: str, force_refresh: bool = False) -> Optional[dict]:
        """
        Fetch current price and basic info for a symbol with caching.

        Args:
            symbol: Stock ticker symbol
            force_refresh: Force refresh from API (ignore cache)

        Returns:
            Dictionary with current price data
        """
        symbol = symbol.upper()

        # Check cache first (current price cached for 1 hour)
        if self.use_cache and not force_refresh:
            cache_path = self._get_cache_path('current', symbol)
            cache_json = cache_path.with_suffix('.json')
            
            if self._is_cache_valid(cache_json, self.current_price_cache_hours):
                try:
                    with open(cache_json, 'r') as f:
                        price_data = json.load(f)
                        price_data['timestamp'] = datetime.fromisoformat(price_data['timestamp'])
                        logger.debug(f"Using cached price for {symbol}: ${price_data['current_price']:.2f}")
                        return price_data
                except Exception as e:
                    logger.debug(f"Cache read failed: {e}")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get the most recent data
            hist = ticker.history(period='1d')

            if hist.empty:
                logger.warning(f"No current data for {symbol}")
                return None

            latest = hist.iloc[-1]

            price_data = {
                'symbol': symbol,
                'current_price': float(latest['Close']),
                'open_price': float(latest['Open']),
                'high_price': float(latest['High']),
                'low_price': float(latest['Low']),
                'close_price': float(latest['Close']),
                'volume': int(latest['Volume']),
                'market_cap': info.get('marketCap'),
                'timestamp': datetime.now()
            }

            logger.debug(f"Current price for {symbol}: ${price_data['current_price']:.2f}")

            # Save to cache
            if self.use_cache:
                cache_json = self._get_cache_path('current', symbol).with_suffix('.json')
                try:
                    # Convert datetime to ISO format for JSON serialization
                    cache_data = price_data.copy()
                    cache_data['timestamp'] = cache_data['timestamp'].isoformat()
                    with open(cache_json, 'w') as f:
                        json.dump(cache_data, f)
                    logger.debug(f"Cached price for {symbol}")
                except Exception as e:
                    logger.warning(f"Cache save failed: {e}")

            return price_data

        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None

    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        days: int = 365
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch historical data for multiple symbols.

        Args:
            symbols: List of stock ticker symbols
            days: Number of days of historical data

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}

        for symbol in symbols:
            df = self.fetch_historical_data(symbol, days)
            if df is not None:
                results[symbol] = df

            # Rate limiting between requests
            time.sleep(self.config.api_call_delay)

        logger.info(f"Fetched data for {len(results)}/{len(symbols)} symbols")

        return results

    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """
        Get detailed stock information.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with stock info
        """
        symbol = symbol.upper()

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            stock_info = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'avg_volume': info.get('averageVolume'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price': info.get('currentPrice'),
            }

            return stock_info

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return None

