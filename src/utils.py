"""
Shared utility functions for NSE option chain processing.
Includes parsing, numeric cleaning, and timestamp helpers.
"""
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any


def clean_numeric(value: Any) -> Optional[float]:
    """
    Clean numeric values from NSE data (handles commas, dashes, etc.)
    
    Args:
        value: Value to clean (can be string, float, int, or None)
        
    Returns:
        Cleaned float value or None if invalid
    """
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # Remove commas and whitespace
        cleaned = value.replace(',', '').strip()
        # Handle dash/empty as None
        if cleaned in ['-', '', 'N/A', 'NA']:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    return None


def parse_timestamp(timestamp_str: str, format_str: Optional[str] = None) -> Optional[datetime]:
    """
    Parse timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string to parse
        format_str: Optional format string (if None, tries common formats)
        
    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None
    
    if format_str:
        try:
            return datetime.strptime(timestamp_str, format_str)
        except ValueError:
            return None
    
    # Try common formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%d-%b-%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None


def parse_strike_data(raw_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parse raw NSE option chain data into strike-level DataFrame.
    
    Args:
        raw_data: Raw data dictionary from NSE API
        
    Returns:
        DataFrame with strike-level option chain data
    """
    records = []
    
    if 'records' not in raw_data or 'data' not in raw_data['records']:
        return pd.DataFrame()
    
    for expiry_data in raw_data['records']['data'].values():
        if 'CE' in expiry_data or 'PE' in expiry_data:
            strike = clean_numeric(expiry_data.get('strikePrice'))
            if strike is None:
                continue
            
            record = {'strike': strike}
            
            # Parse Call option data
            if 'CE' in expiry_data:
                ce = expiry_data['CE']
                record.update({
                    'ce_oi': clean_numeric(ce.get('openInterest')),
                    'ce_change_oi': clean_numeric(ce.get('changeinOpenInterest')),
                    'ce_volume': clean_numeric(ce.get('totalTradedVolume')),
                    'ce_iv': clean_numeric(ce.get('impliedVolatility')),
                    'ce_ltp': clean_numeric(ce.get('lastPrice')),
                    'ce_bid': clean_numeric(ce.get('bidprice')),
                    'ce_ask': clean_numeric(ce.get('askPrice')),
                })
            
            # Parse Put option data
            if 'PE' in expiry_data:
                pe = expiry_data['PE']
                record.update({
                    'pe_oi': clean_numeric(pe.get('openInterest')),
                    'pe_change_oi': clean_numeric(pe.get('changeinOpenInterest')),
                    'pe_volume': clean_numeric(pe.get('totalTradedVolume')),
                    'pe_iv': clean_numeric(pe.get('impliedVolatility')),
                    'pe_ltp': clean_numeric(pe.get('lastPrice')),
                    'pe_bid': clean_numeric(pe.get('bidprice')),
                    'pe_ask': clean_numeric(pe.get('askPrice')),
                })
            
            records.append(record)
    
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    return df.sort_values('strike').reset_index(drop=True)


def get_atm_strike(spot: float, strikes: pd.Series) -> float:
    """
    Find the closest strike to spot price (ATM proxy).
    
    Args:
        spot: Current spot price
        strikes: Series of available strikes
        
    Returns:
        Closest strike price
    """
    if strikes.empty:
        return spot
    
    return strikes.iloc[(strikes - spot).abs().argsort()].iloc[0]


def calculate_pcr(call_oi: float, put_oi: float) -> Optional[float]:
    """
    Calculate Put-Call Ratio.
    
    Args:
        call_oi: Total call open interest
        put_oi: Total put open interest
        
    Returns:
        PCR value or None if invalid
    """
    if call_oi is None or put_oi is None or call_oi == 0:
        return None
    return put_oi / call_oi



