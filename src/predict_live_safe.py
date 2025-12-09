"""
Safe version that handles LightGBM import errors gracefully.
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run live prediction with error handling."""
    symbol = sys.argv[1] if len(sys.argv) > 1 else "NIFTY"
    
    print(f"=" * 60)
    print(f"NSE Option Chain Predictor - Live Prediction")
    print(f"=" * 60)
    print(f"Symbol: {symbol}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"=" * 60)
    print()
    
    # Try to import predictor
    try:
        # Check LightGBM first
        try:
            import lightgbm as lgb
        except (ImportError, FileNotFoundError, OSError) as lgb_error:
            raise ImportError(f"LightGBM import failed: {lgb_error}")
        
        from src.fetch_predict import OptionChainPredictor
    except (ImportError, FileNotFoundError, OSError) as e:
        if "lightgbm" in str(e).lower():
            print("❌ LightGBM Import Error")
            print()
            print("Python 3.13 has compatibility issues with LightGBM on Windows.")
            print("Solutions:")
            print("  1. Use Python 3.11 or 3.12 (recommended)")
            print("  2. Install via conda: conda install -c conda-forge lightgbm")
            print("  3. Use WSL (Windows Subsystem for Linux)")
            print()
            print("However, you can still test data fetching...")
            print()
            
            # Try to test data fetching without model
            try:
                import requests
                print("Testing NSE API connection...")
                session = requests.Session()
                session.headers.update({
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json"
                })
                session.get("https://www.nseindia.com")
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    spot = data.get('records', {}).get('underlyingValue')
                    if spot:
                        print(f"✓ Successfully fetched data!")
                        print(f"  Spot Price: ₹{spot}")
                        print(f"  Market appears to be open")
                    else:
                        print("✓ API accessible but market may be closed")
                else:
                    print(f"⚠ API returned status {response.status_code}")
                    print("  Market may be closed or API restricted")
            except Exception as fetch_error:
                print(f"⚠ Could not fetch data: {fetch_error}")
                print("  Market is likely closed (NSE hours: 9:15 AM - 3:30 PM IST)")
            
            sys.exit(1)
        else:
            print(f"❌ Import Error: {e}")
            sys.exit(1)
    
    try:
        # Initialize predictor
        print("Loading model...")
        predictor = OptionChainPredictor()
        
        if predictor.model is None:
            print("⚠️  Warning: Model not loaded. Check if model files exist in models/ directory")
            print("   Required files:")
            print("   - lgb_model_oversampled.txt")
            print("   - label_encoder_oversampled.joblib")
            print("   - features_oversampled.json")
            return
        
        print("✓ Model loaded successfully")
        print()
        
        # Fetch and predict
        print(f"Fetching option chain data for {symbol}...")
        result = predictor.fetch_and_predict(symbol)
        
        if result is None:
            print("❌ Failed to fetch option chain data")
            print()
            print("Possible reasons:")
            print("1. Market is closed (NSE hours: 9:15 AM - 3:30 PM IST)")
            print("2. Network connectivity issues")
            print("3. NSE API is temporarily unavailable")
            print()
            print("💡 Tip: Try again during market hours (9:15 AM - 3:30 PM IST)")
            return
        
        print("✓ Data fetched successfully")
        print()
        
        # Display results
        print("=" * 60)
        print("PREDICTION RESULTS")
        print("=" * 60)
        
        if result.get('predicted_class'):
            print(f"Predicted Class: {result['predicted_class']}")
        else:
            print(f"Predicted Class Index: {result.get('predicted_class_idx', 'N/A')}")
        
        print(f"Spot Price: ₹{result.get('spot', 'N/A'):.2f}" if result.get('spot') else "Spot Price: N/A")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")
        print()
        
        if result.get('probabilities'):
            print("Class Probabilities:")
            for idx, prob in enumerate(result['probabilities']):
                print(f"  Class {idx}: {prob:.4f} ({prob*100:.2f}%)")
            print()
        
        if result.get('features'):
            print("Key Features:")
            key_features = ['spot', 'pcr', 'total_call_oi', 'total_put_oi', 'median_iv', 'atm_strike']
            for feat in key_features:
                if feat in result['features']:
                    value = result['features'][feat]
                    if isinstance(value, float):
                        print(f"  {feat}: {value:.2f}")
                    else:
                        print(f"  {feat}: {value}")
        
        print("=" * 60)
        
        # Save to file (optional)
        output_file = f"prediction_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n✓ Results saved to {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

