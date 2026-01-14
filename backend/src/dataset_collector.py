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
        
        # Create combined dataset (removing duplicates)
        if datasets:
            combined = pd.concat(datasets.values(), ignore_index=True)
            combined = combined.drop_duplicates(subset=['symbol'], keep='first')
            datasets['COMBINED'] = combined
            
            filepath = self.data_dir / "combined_companies.csv"
            combined.to_csv(filepath, index=False)
            logger.success(f"Saved combined dataset ({len(combined)} companies) to {filepath}")
        
        return datasets

    def load_dataset(self, dataset_name: str = "COMBINED") -> Optional[pd.DataFrame]:
        """
        Load a previously saved dataset.
        
        Args:
            dataset_name: Name of dataset ('SP500', 'NASDAQ100', or 'COMBINED')
            
        Returns:
            DataFrame or None if not found
        """
        filename_map = {
            'SP500': 'sp500_companies.csv',
            'NASDAQ100': 'nasdaq100_companies.csv',
            'COMBINED': 'combined_companies.csv'
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
