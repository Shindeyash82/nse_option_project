"""
Test script to fetch NSE option chain data without requiring LightGBM.
Useful for testing during market hours or after hours.
"""
import requests
import json
from datetime import datetime, time


def fetch_option_chain(symbol="NIFTY"):
    """Fetch option chain data from NSE API."""
    print(f"=" * 60)
    print(f"Testing NSE Option Chain Data Fetch")
    print(f"=" * 60)
    print(f"Symbol: {symbol}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 60)
    print()
    
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        print("Connecting to NSE API...")
        session = requests.Session()
        session.headers.update(headers)
        
        # First request to get cookies
        print("Getting session cookies...")
        session.get("https://www.nseindia.com", timeout=10)
        
        print(f"Fetching option chain data for {symbol}...")
        response = session.get(url, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract key information
            records = data.get('records', {})
            spot = records.get('underlyingValue')
            timestamp = records.get('timestamp')
            
            print()
            print("=" * 60)
            print("SUCCESS - Data Retrieved")
            print("=" * 60)
            
            if spot:
                print(f"✓ Spot Price: ₹{spot}")
            else:
                print("⚠ Spot price not available")
            
            if timestamp:
                print(f"✓ Timestamp: {timestamp}")
            
            # Count expiries
            expiries = records.get('expiryDates', [])
            print(f"✓ Expiry Dates: {len(expiries)} available")
            if expiries:
                print(f"  Next expiry: {expiries[0]}")
            
            # Check if market is open
            now = datetime.now().time()
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            if market_open <= now <= market_close:
                print("✓ Market Status: OPEN (9:15 AM - 3:30 PM IST)")
            else:
                print("⚠ Market Status: CLOSED (Current time outside trading hours)")
            
            print()
            print("=" * 60)
            print("Sample Data Structure:")
            print("=" * 60)
            print(json.dumps({
                "spot": spot,
                "timestamp": timestamp,
                "expiries_count": len(expiries),
                "has_data": bool(records.get('data'))
            }, indent=2))
            
            return True
            
        elif response.status_code == 403:
            print()
            print("=" * 60)
            print("ACCESS FORBIDDEN")
            print("=" * 60)
            print("NSE API returned 403 Forbidden.")
            print("Possible reasons:")
            print("1. Market is closed")
            print("2. API access is restricted")
            print("3. Rate limiting")
            print()
            print("💡 Try again during market hours (9:15 AM - 3:30 PM IST)")
            return False
            
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print()
        print("=" * 60)
        print("TIMEOUT ERROR")
        print("=" * 60)
        print("Request timed out. Check your internet connection.")
        return False
        
    except requests.exceptions.ConnectionError:
        print()
        print("=" * 60)
        print("CONNECTION ERROR")
        print("=" * 60)
        print("Could not connect to NSE API.")
        print("Check your internet connection.")
        return False
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "NIFTY"
    fetch_option_chain(symbol)

