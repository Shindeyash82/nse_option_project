"""
Collector loop: fetch option-chain, parse, save aggregated snapshots.
Supports --once flag for single run.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import argparse
import time
from datetime import datetime
from typing import Optional
from src.fetch_predict import OptionChainPredictor
from src.utils import parse_strike_data, clean_numeric


class OptionChainCollector:
    """Collects and saves aggregated option chain snapshots."""
    
    def __init__(self, data_dir: str = "data/processed", symbol: str = "NIFTY"):
        """
        Initialize collector.
        
        Args:
            data_dir: Directory to save processed data
            symbol: Option symbol to collect
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.symbol = symbol
        self.predictor = OptionChainPredictor()
    
    def collect_snapshot(self) -> Optional[pd.DataFrame]:
        """
        Collect a single snapshot and return as DataFrame.
        
        Returns:
            DataFrame with aggregated features or None if fetch fails
        """
        # Fetch option chain
        raw_data = self.predictor.fetch_option_chain(self.symbol)
        if raw_data is None:
            return None
        
        # Extract spot
        spot = clean_numeric(raw_data.get('records', {}).get('underlyingValue'))
        if spot is None:
            return None
        
        # Parse strike data
        strike_df = parse_strike_data(raw_data)
        if strike_df.empty:
            return None
        
        # Aggregate features
        features = self.predictor.aggregate_features(strike_df, spot)
        
        # Add metadata
        features['timestamp'] = datetime.now()
        features['symbol'] = self.symbol
        
        # Convert to DataFrame
        snapshot_df = pd.DataFrame([features])
        return snapshot_df
    
    def save_snapshot(self, snapshot_df: pd.DataFrame, format: str = "parquet"):
        """
        Save snapshot to disk.
        
        Args:
            snapshot_df: DataFrame to save
            format: File format ('parquet' or 'csv')
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.symbol}_{timestamp}.{format}"
        filepath = self.data_dir / filename
        
        if format == "parquet":
            snapshot_df.to_parquet(filepath, index=False)
        else:
            snapshot_df.to_csv(filepath, index=False)
        
        print(f"Saved snapshot to {filepath}")
    
    def run_once(self, save: bool = True) -> Optional[pd.DataFrame]:
        """
        Collect a single snapshot.
        
        Args:
            save: Whether to save to disk
            
        Returns:
            Snapshot DataFrame or None
        """
        print(f"Collecting snapshot for {self.symbol}...")
        snapshot_df = self.collect_snapshot()
        
        if snapshot_df is not None:
            print(f"Snapshot collected: {len(snapshot_df)} rows")
            if save:
                self.save_snapshot(snapshot_df)
            return snapshot_df
        else:
            print("Failed to collect snapshot")
            return None
    
    def run_continuous(self, interval: float = 60.0, max_snapshots: Optional[int] = None):
        """
        Run continuous collection loop.
        
        Args:
            interval: Collection interval in seconds
            max_snapshots: Maximum snapshots to collect (None = unlimited)
        """
        print(f"Starting continuous collection for {self.symbol}")
        print(f"Interval: {interval}s")
        if max_snapshots:
            print(f"Max snapshots: {max_snapshots}")
        
        snapshot_count = 0
        
        try:
            while True:
                if max_snapshots and snapshot_count >= max_snapshots:
                    print(f"Reached max snapshots ({max_snapshots}). Stopping.")
                    break
                
                snapshot_df = self.run_once(save=True)
                if snapshot_df is not None:
                    snapshot_count += 1
                
                print(f"Waiting {interval}s until next collection...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\nStopping collector...")
        finally:
            print(f"Collection stopped. Total snapshots: {snapshot_count}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="NSE Option Chain Collector")
    parser.add_argument("--symbol", default="NIFTY", help="Option symbol (default: NIFTY)")
    parser.add_argument("--data-dir", default="data/processed", help="Data directory")
    parser.add_argument("--interval", type=float, default=60.0, help="Collection interval in seconds")
    parser.add_argument("--max-snapshots", type=int, help="Maximum snapshots to collect")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet", help="File format")
    
    args = parser.parse_args()
    
    collector = OptionChainCollector(data_dir=args.data_dir, symbol=args.symbol)
    
    if args.once:
        collector.run_once(save=True)
    else:
        collector.run_continuous(interval=args.interval, max_snapshots=args.max_snapshots)


if __name__ == "__main__":
    main()

