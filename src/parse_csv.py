"""
CSV parser: parse NSE .csv downloads into strike-level DataFrame.
Optional utility for processing manually downloaded CSV files.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List
from src.utils import clean_numeric, parse_timestamp


def parse_nse_csv(csv_path: str) -> Optional[pd.DataFrame]:
    """
    Parse NSE option chain CSV file into strike-level DataFrame.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        DataFrame with strike-level option data or None if parsing fails
    """
    try:
        # Read CSV - NSE CSV files may have multiple header rows
        df = pd.read_csv(csv_path, skiprows=1)  # Skip first row if it's a header
        
        # Common NSE CSV column names (may vary)
        # Adjust these based on actual CSV structure
        column_mapping = {
            'Strike Price': 'strike',
            'Strike': 'strike',
            'CALLS OI': 'ce_oi',
            'CALLS Change in OI': 'ce_change_oi',
            'CALLS Volume': 'ce_volume',
            'CALLS IV': 'ce_iv',
            'CALLS LTP': 'ce_ltp',
            'CALLS Bid': 'ce_bid',
            'CALLS Ask': 'ce_ask',
            'PUTS OI': 'pe_oi',
            'PUTS Change in OI': 'pe_change_oi',
            'PUTS Volume': 'pe_volume',
            'PUTS IV': 'pe_iv',
            'PUTS LTP': 'pe_ltp',
            'PUTS Bid': 'pe_bid',
            'PUTS Ask': 'pe_ask',
        }
        
        # Rename columns if mapping exists
        df = df.rename(columns=column_mapping)
        
        # Ensure strike column exists
        if 'strike' not in df.columns:
            # Try to find strike column
            strike_cols = [col for col in df.columns if 'strike' in col.lower() or 'strike' in col.lower()]
            if strike_cols:
                df['strike'] = df[strike_cols[0]]
            else:
                print("Warning: Could not find strike column")
                return None
        
        # Clean numeric columns
        numeric_cols = ['strike', 'ce_oi', 'ce_change_oi', 'ce_volume', 'ce_iv', 'ce_ltp', 
                       'ce_bid', 'ce_ask', 'pe_oi', 'pe_change_oi', 'pe_volume', 'pe_iv', 
                       'pe_ltp', 'pe_bid', 'pe_ask']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_numeric)
        
        # Remove rows with invalid strikes
        df = df[df['strike'].notna()].copy()
        df = df.sort_values('strike').reset_index(drop=True)
        
        return df
    
    except Exception as e:
        print(f"Error parsing CSV file {csv_path}: {e}")
        return None


def batch_parse_csv(csv_dir: str, output_dir: Optional[str] = None, format: str = "parquet") -> List[pd.DataFrame]:
    """
    Parse multiple CSV files from a directory.
    
    Args:
        csv_dir: Directory containing CSV files
        output_dir: Optional directory to save parsed files
        format: Output format ('parquet' or 'csv')
        
    Returns:
        List of parsed DataFrames
    """
    csv_path = Path(csv_dir)
    if not csv_path.exists():
        print(f"Directory {csv_dir} does not exist")
        return []
    
    csv_files = list(csv_path.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {csv_dir}")
        return []
    
    parsed_dfs = []
    
    for csv_file in csv_files:
        print(f"Parsing {csv_file.name}...")
        df = parse_nse_csv(str(csv_file))
        
        if df is not None and not df.empty:
            parsed_dfs.append(df)
            
            # Save if output directory specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                output_file = output_path / f"{csv_file.stem}.{format}"
                if format == "parquet":
                    df.to_parquet(output_file, index=False)
                else:
                    df.to_csv(output_file, index=False)
                print(f"Saved to {output_file}")
    
    print(f"Parsed {len(parsed_dfs)} CSV files")
    return parsed_dfs


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse NSE option chain CSV files")
    parser.add_argument("csv_path", help="Path to CSV file or directory")
    parser.add_argument("--output-dir", help="Output directory for parsed files")
    parser.add_argument("--format", choices=["parquet", "csv"], default="parquet", help="Output format")
    parser.add_argument("--batch", action="store_true", help="Process directory of CSV files")
    
    args = parser.parse_args()
    
    if args.batch:
        dfs = batch_parse_csv(args.csv_path, args.output_dir, args.format)
        print(f"Total rows parsed: {sum(len(df) for df in dfs)}")
    else:
        df = parse_nse_csv(args.csv_path)
        if df is not None:
            print(f"Parsed {len(df)} rows")
            print(df.head())
            
            if args.output_dir:
                output_path = Path(args.output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                output_file = output_path / f"parsed_{Path(args.csv_path).stem}.{args.format}"
                if args.format == "parquet":
                    df.to_parquet(output_file, index=False)
                else:
                    df.to_csv(output_file, index=False)
                print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()



