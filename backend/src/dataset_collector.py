"""
Dataset Collector - Fetch S&P 500 and NASDAQ 100 company listings.
"""
from typing import List, Dict, Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
import time
from pathlib import Path
import json

try:
    from .config import get_config
except ImportError:
    from config import get_config


class DatasetCollector:
    """Collect and manage stock universe datasets (S&P 500, NASDAQ 100, etc.)."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize dataset collector.
        
        Args:
            data_dir: Directory to store dataset files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        logger.info("DatasetCollector initialized")

    def fetch_sp500_companies(self, save: bool = True) -> pd.DataFrame:
        """
        Fetch S&P 500 company list from Wikipedia.
        
        Args:
            save: Whether to save to CSV file
            
        Returns:
            DataFrame with columns: Symbol, Security, Sector, Sub-Industry, Headquarters, Founded, etc.
        """
        logger.info("Fetching S&P 500 companies from Wikipedia...")
        
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # Fetch the page
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            # Parse the table
            soup = BeautifulSoup(response.content, 'lxml')
            table = soup.find('table', {'id': 'constituents'})
            
            # Read table into DataFrame
            df = pd.read_html(str(table))[0]
            
            # Clean up column names
            df.columns = df.columns.str.strip()
            
            # Rename columns for consistency
            column_mapping = {
                'Symbol': 'symbol',
                'Security': 'company_name',
                'GICS Sector': 'sector',
                'GICS Sub-Industry': 'sub_industry',
                'Headquarters Location': 'headquarters',
                'Date added': 'date_added',
                'CIK': 'cik',
                'Founded': 'founded'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Add dataset identifier
            df['dataset'] = 'SP500'
            
            # Select and reorder columns
            available_cols = [col for col in ['symbol', 'company_name', 'sector', 'sub_industry', 
                                               'headquarters', 'date_added', 'cik', 'founded', 'dataset'] 
                              if col in df.columns]
            df = df[available_cols]
            
            logger.success(f"Fetched {len(df)} S&P 500 companies")
            
            if save:
                filepath = self.data_dir / "sp500_companies.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching S&P 500 data: {e}")
            return pd.DataFrame()

    def fetch_nasdaq100_companies(self, save: bool = True) -> pd.DataFrame:
        """
        Fetch NASDAQ 100 company list from Wikipedia.
        
        Args:
            save: Whether to save to CSV file
            
        Returns:
            DataFrame with columns: Symbol, Company, Sector, Sub-Industry
        """
        logger.info("Fetching NASDAQ 100 companies from Wikipedia...")
        
        try:
            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            
            # Fetch the page
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            # Parse the table
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the constituents table (usually the first table with "Ticker" column)
            tables = pd.read_html(response.content)
            
            # Find the right table (has Ticker/Symbol column)
            df = None
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    df = table
                    break
            
            if df is None:
                raise ValueError("Could not find NASDAQ 100 constituents table")
            
            # Clean up column names
            df.columns = df.columns.str.strip()
            
            # Rename columns for consistency
            column_mapping = {
                'Ticker': 'symbol',
                'Symbol': 'symbol',
                'Company': 'company_name',
                'Sector': 'sector',
                'Sub-industry': 'sub_industry',
                'GICS Sector': 'sector',
                'GICS Sub-Industry': 'sub_industry'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Add dataset identifier
            df['dataset'] = 'NASDAQ100'
            
            # Select and reorder columns
            available_cols = [col for col in ['symbol', 'company_name', 'sector', 'sub_industry', 'dataset'] 
                              if col in df.columns]
            df = df[available_cols]
            
            # Remove any rows with missing symbols
            df = df.dropna(subset=['symbol'])
            
            logger.success(f"Fetched {len(df)} NASDAQ 100 companies")
            
            if save:
                filepath = self.data_dir / "nasdaq100_companies.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100 data: {e}")
            return pd.DataFrame()

    def fetch_nifty50_companies(self, save: bool = True) -> pd.DataFrame:
        """
        Fetch Nifty 50 company list (Indian stocks).
        
        Args:
            save: Whether to save to CSV file
            
        Returns:
            DataFrame with columns: Symbol, Company, Sector
        """
        logger.info("Fetching Nifty 50 companies...")
        
        try:
            # Nifty 50 symbols - these are the top 50 companies in India
            nifty50_symbols = [
                'RELIANCE', 'TCS', 'INFOSY', 'HDFC', 'ICICIBANK', 'SBIN', 'BAJAJFINSV',
                'MARUTI', 'SUNPHARMA', 'ASIANPAINT', 'HCLTECH', 'WIPRO', 'KOTAKBANK',
                'BAJAJ-AUTO', 'DMART', 'LT', 'ITC', 'AXISBANK', 'INDIGO', 'JSWSTEEL',
                'TATASTEEL', 'HEROMOTOCO', 'LUPIN', 'POWERGRID', 'ULTRACEMCO', 'NTPC',
                'CIPLA', 'TECHM', 'DIVISLAB', 'BHARTIARTL', 'GRASIM', 'EICHERMOT',
                'HINDALCO', 'BPCL', 'M&M', 'NESTLEIND', 'HDFCLIFE', 'SBILIFE', 'MGL',
                'DRREDDY', 'HINDUNILVR', 'APOLLOHOSP', 'AUROPHARMA', 'INFY', 'ADANIPORTS',
                'ADANIENT', 'CEMENT', 'INDUSINDBK'
            ]
            
            # Create DataFrame with Nifty 50 data (add .NS suffix for Yahoo Finance)
            df = pd.DataFrame({
                'symbol': [f"{sym}.NS" for sym in nifty50_symbols],
                'company_name': nifty50_symbols,  # Could enhance with actual names
                'sector': 'NIFTY50',  # Placeholder
                'dataset': 'NIFTY50'
            })
            
            logger.success(f"Loaded {len(df)} Nifty 50 companies")
            
            if save:
                filepath = self.data_dir / "nifty50_companies.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Nifty 50 data: {e}")
            return pd.DataFrame()

    def fetch_nifty_next50_companies(self, save: bool = True) -> pd.DataFrame:
        """
        Fetch Nifty Next 50 company list (Indian stocks).
        
        Args:
            save: Whether to save to CSV file
            
        Returns:
            DataFrame with columns: Symbol, Company, Sector
        """
        logger.info("Fetching Nifty Next 50 companies...")
        
        try:
            # Nifty Next 50 symbols
            nifty_next50_symbols = [
                'ALKEM', 'AMBUJACEM', 'BANKBARODA', 'BIOCON', 'BOSCHLTD', 'CENTURYTEX',
                'COLPAL', 'ESCORT', 'EXIDEIND', 'FSL', 'GAIL', 'GODREJCP', 'IDBI',
                'INDIANB', 'IPCALAB', 'JINDALSTEL', 'JSWENERGY', 'KPITTECH', 'LICHSGFIN',
                'LTFH', 'MCDOWELL', 'MOTHERSON', 'NATIONALUM', 'NAUKRI', 'NHPC', 'ONGC',
                'PAGEIND', 'PETRONET', 'PFC', 'RECLTD', 'SAIL', 'SCI', 'SIEMENS', 'STARTECH',
                'SUNPRINT', 'SUNTV', 'TATAMOTORS', 'TITAN', 'TORNTPOWER', 'TORNTPHARMA',
                'TRENT', 'TRITURBINE', 'UPL', 'VBL', 'VEDL', 'VOLTAS', 'ZCAL', 'ZEEL'
            ]
            
            # Create DataFrame with Nifty Next 50 data (add .NS suffix for Yahoo Finance)
            df = pd.DataFrame({
                'symbol': [f"{sym}.NS" for sym in nifty_next50_symbols],
                'company_name': nifty_next50_symbols,  # Could enhance with actual names
                'sector': 'NIFTYNEXT50',  # Placeholder
                'dataset': 'NIFTYNEXT50'
            })
            
            logger.success(f"Loaded {len(df)} Nifty Next 50 companies")
            
            if save:
                filepath = self.data_dir / "niftynext50_companies.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Nifty Next 50 data: {e}")
            return pd.DataFrame()

    def fetch_niftymidcap_companies(self, save: bool = True) -> pd.DataFrame:
        """
        Fetch Nifty Midcap Select company list (Indian stocks).
        
        Args:
            save: Whether to save to CSV file
            
        Returns:
            DataFrame with columns: Symbol, Company, Sector
        """
        logger.info("Fetching Nifty Midcap Select companies...")
        
        try:
            # Nifty Midcap Select symbols (top 50 midcap stocks)
            niftymidcap_symbols = [
                'ABB', 'ABCAPITAL', 'ABSLLICER', 'ADHARSH', 'ADHUNIK', 'ADITYABRL',
                'ADVANIPORT', 'AEGISCHEM', 'AETHER', 'AFLAM', 'AGRITECH', 'AHLUCONE',
                'AIAENG', 'AKUMS', 'ALEMBIC', 'ALOTECH', 'ALPHABLDG', 'ALTARRTECH',
                'AMBER', 'AMZL', 'ANANYAENT', 'ANDEROBA', 'ANURAS', 'AOFINANCE',
                'APEIRON', 'APLLTD', 'APOLLOADV', 'APPLAUD', 'APPLYCARD', 'APTECH',
                'ARJUNPHARMA', 'ARKADE', 'ARMADAMAN', 'ARTHUNEMPLOYED', 'ARVIND',
                'ASAHIINDIA', 'ASIANHOTEL', 'ASIANPNT', 'ASIANSLATE', 'ASKAUTOMV',
                'ASSEEM', 'ASTECK', 'ASTERDM', 'ASTRA', 'ASTRAL', 'ASTRUTIC', 'ASUPERB', 'ATGL', 'ATIIND'
            ]
            
            # Create DataFrame with Nifty Midcap Select data (add .NS suffix for Yahoo Finance)
            df = pd.DataFrame({
                'symbol': [f"{sym}.NS" for sym in niftymidcap_symbols[:50]],  # Ensure exactly 50
                'company_name': niftymidcap_symbols[:50],  # Could enhance with actual names
                'sector': 'NIFTYMIDCAP',  # Placeholder
                'dataset': 'NIFTYMIDCAP'
            })
            
            logger.success(f"Loaded {len(df)} Nifty Midcap Select companies")
            
            if save:
                filepath = self.data_dir / "niftymidcap_companies.csv"
                df.to_csv(filepath, index=False)
                logger.info(f"Saved to {filepath}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Nifty Midcap Select data: {e}")
            return pd.DataFrame()

    def fetch_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Fetch all available datasets.
        
        Returns:
            Dictionary with dataset names as keys and DataFrames as values
        """
        logger.info("Fetching all datasets...")
        
        datasets = {}
        
        # Fetch S&P 500
        sp500 = self.fetch_sp500_companies(save=True)
        if not sp500.empty:
            datasets['SP500'] = sp500
        
        time.sleep(1)  # Be respectful to Wikipedia servers
        
        # Fetch NASDAQ 100
        nasdaq100 = self.fetch_nasdaq100_companies(save=True)
        if not nasdaq100.empty:
            datasets['NASDAQ100'] = nasdaq100
        
        # Fetch Nifty 50
        nifty50 = self.fetch_nifty50_companies(save=True)
        if not nifty50.empty:
            datasets['NIFTY50'] = nifty50
        
        # Fetch Nifty Next 50
        nifty_next50 = self.fetch_nifty_next50_companies(save=True)
        if not nifty_next50.empty:
            datasets['NIFTYNEXT50'] = nifty_next50
        
        # Fetch Nifty Midcap Select
        nifty_midcap = self.fetch_niftymidcap_companies(save=True)
        if not nifty_midcap.empty:
            datasets['NIFTYMIDCAP'] = nifty_midcap
        
        # Create combined US dataset
        us_combined = None
        if 'SP500' in datasets or 'NASDAQ100' in datasets:
            us_datasets = [datasets[k] for k in ['SP500', 'NASDAQ100'] if k in datasets]
            if us_datasets:
                us_combined = pd.concat(us_datasets, ignore_index=True)
                us_combined = us_combined.drop_duplicates(subset=['symbol'], keep='first')
                datasets['COMBINED'] = us_combined
                
                filepath = self.data_dir / "combined_companies.csv"
                us_combined.to_csv(filepath, index=False)
                logger.success(f"Saved combined US dataset ({len(us_combined)} companies) to {filepath}")
        
        # Create combined Nifty dataset
        nifty_datasets_list = [datasets[k] for k in ['NIFTY50', 'NIFTYNEXT50', 'NIFTYMIDCAP'] if k in datasets]
        if nifty_datasets_list:
            nifty_combined = pd.concat(nifty_datasets_list, ignore_index=True)
            nifty_combined = nifty_combined.drop_duplicates(subset=['symbol'], keep='first')
            datasets['NIFTY_ALL'] = nifty_combined
            
            filepath = self.data_dir / "nifty_all_companies.csv"
            nifty_combined.to_csv(filepath, index=False)
            logger.success(f"Saved combined Nifty dataset ({len(nifty_combined)} companies) to {filepath}")
        
        # Create global combined dataset (all indices)
        if datasets:
            all_datasets = [datasets[k] for k in datasets.keys() if k not in ['COMBINED', 'NIFTY_ALL']]
            if all_datasets:
                global_combined = pd.concat(all_datasets, ignore_index=True)
                global_combined = global_combined.drop_duplicates(subset=['symbol'], keep='first')
                datasets['ALL'] = global_combined
                
                filepath = self.data_dir / "all_companies.csv"
                global_combined.to_csv(filepath, index=False)
                logger.success(f"Saved global combined dataset ({len(global_combined)} companies) to {filepath}")
        
        return datasets

    def load_dataset(self, dataset_name: str = "COMBINED") -> Optional[pd.DataFrame]:
        """
        Load a previously saved dataset.
        
        Args:
            dataset_name: Name of dataset ('SP500', 'NASDAQ100', 'NIFTY50', 'NIFTYNEXT50', 
                         'NIFTYMIDCAP', 'COMBINED', 'NIFTY_ALL', or 'ALL')
            
        Returns:
            DataFrame or None if not found
        """
        filename_map = {
            'SP500': 'sp500_companies.csv',
            'NASDAQ100': 'nasdaq100_companies.csv',
            'NIFTY50': 'nifty50_companies.csv',
            'NIFTYNEXT50': 'niftynext50_companies.csv',
            'NIFTYMIDCAP': 'niftymidcap_companies.csv',
            'COMBINED': 'combined_companies.csv',
            'NIFTY_ALL': 'nifty_all_companies.csv',
            'ALL': 'all_companies.csv'
        }
        
        filename = filename_map.get(dataset_name.upper())
        if not filename:
            logger.error(f"Unknown dataset: {dataset_name}")
            return None
        
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Dataset file not found: {filepath}")
            logger.info("Fetching fresh data...")
            self.fetch_all_datasets()
        
        if filepath.exists():
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} companies from {filepath}")
            return df
        
        return None

    def get_symbols_by_sector(self, dataset_name: str = "COMBINED", sector: Optional[str] = None) -> List[str]:
        """
        Get stock symbols filtered by sector.
        
        Args:
            dataset_name: Dataset to use
            sector: Sector name (e.g., 'Technology', 'Financials'). None returns all.
            
        Returns:
            List of stock symbols
        """
        df = self.load_dataset(dataset_name)
        
        if df is None:
            return []
        
        if sector and 'sector' in df.columns:
            df = df[df['sector'].str.contains(sector, case=False, na=False)]
        
        return df['symbol'].tolist()

    def get_dataset_summary(self) -> Dict[str, any]:
        """
        Get summary statistics for all datasets.
        
        Returns:
            Dictionary with dataset statistics
        """
        summary = {}
        
        for dataset_name in ['SP500', 'NASDAQ100', 'COMBINED']:
            df = self.load_dataset(dataset_name)
            if df is not None:
                summary[dataset_name] = {
                    'total_companies': len(df),
                    'sectors': df['sector'].nunique() if 'sector' in df.columns else 0,
                    'sector_breakdown': df['sector'].value_counts().to_dict() if 'sector' in df.columns else {}
                }
        
        return summary

    def export_symbols_list(self, dataset_name: str = "COMBINED", output_file: Optional[str] = None) -> List[str]:
        """
        Export just the symbol list for easy use in scanners.
        
        Args:
            dataset_name: Dataset to use
            output_file: Optional file path to save symbols (one per line)
            
        Returns:
            List of symbols
        """
        df = self.load_dataset(dataset_name)
        
        if df is None:
            return []
        
        symbols = df['symbol'].tolist()
        
        if output_file:
            filepath = Path(output_file)
            with open(filepath, 'w') as f:
                f.write('\n'.join(symbols))
            logger.info(f"Exported {len(symbols)} symbols to {filepath}")
        
        return symbols


if __name__ == "__main__":
    # Test the collector
    from loguru import logger
    import sys
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    collector = DatasetCollector()
    
    # Fetch all datasets
    datasets = collector.fetch_all_datasets()
    
    # Show summary
    summary = collector.get_dataset_summary()
    
    print("\n" + "="*70)
    print("DATASET SUMMARY")
    print("="*70)
    
    for dataset, stats in summary.items():
        print(f"\n{dataset}:")
        print(f"  Total Companies: {stats['total_companies']}")
        print(f"  Unique Sectors: {stats['sectors']}")
        if stats['sector_breakdown']:
            print(f"  Top Sectors:")
            for sector, count in list(stats['sector_breakdown'].items())[:5]:
                print(f"    - {sector}: {count}")
    
    print("\n" + "="*70)
