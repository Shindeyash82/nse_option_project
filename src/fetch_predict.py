"""
In-memory fetch → aggregate → predict pipeline.
No disk writes - designed for real-time predictions.
"""
import pandas as pd
import numpy as np
import requests
import json
from typing import Dict, Optional, Any
from datetime import datetime
import lightgbm as lgb
import joblib
import os

from src.utils import parse_strike_data, clean_numeric, get_atm_strike, calculate_pcr


class OptionChainPredictor:
    """In-memory option chain fetcher and predictor."""
    
    def __init__(self, model_dir: str = "models"):
        """
        Initialize predictor with trained model.
        
        Args:
            model_dir: Directory containing model files
        """
        self.model_dir = model_dir
        self.model = None
        self.label_encoder = None
        self.features = None
        self.load_model()
    
    def load_model(self):
        """Load trained model, label encoder, and feature list."""
        model_path = os.path.join(self.model_dir, "lgb_model_oversampled.txt")
        encoder_path = os.path.join(self.model_dir, "label_encoder_oversampled.joblib")
        features_path = os.path.join(self.model_dir, "features_oversampled.json")
        
        if os.path.exists(model_path):
            self.model = lgb.Booster(model_file=model_path)
        
        if os.path.exists(encoder_path):
            self.label_encoder = joblib.load(encoder_path)
        
        if os.path.exists(features_path):
            with open(features_path, 'r') as f:
                self.features = json.load(f)
    
    def fetch_option_chain(self, symbol: str = "NIFTY", base_url: str = None) -> Optional[Dict]:
        """
        Fetch option chain data from NSE API.
        
        Args:
            symbol: Option symbol (default: NIFTY)
            base_url: Base URL for NSE API
            
        Returns:
            Raw option chain data dictionary or None if fetch fails
        """
        if base_url is None:
            base_url = os.getenv("NSE_BASE_URL", "https://www.nseindia.com/api/option-chain-indices")
        
        url = f"{base_url}?symbol={symbol}"
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            session = requests.Session()
            session.headers.update(headers)
            # First request to get cookies
            session.get("https://www.nseindia.com")
            response = session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if market is closed or data is empty
            if not data or 'records' not in data:
                print("Warning: Empty response from NSE API (market may be closed)")
                return None
            
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("Error: Access forbidden. Market may be closed or API access restricted.")
            else:
                print(f"HTTP Error fetching option chain: {e}")
            return None
        except requests.exceptions.Timeout:
            print("Error: Request timeout. Check your internet connection.")
            return None
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            return None
    
    def aggregate_features(self, strike_df: pd.DataFrame, spot: float) -> Dict[str, float]:
        """
        Aggregate strike-level data into snapshot features.
        
        Args:
            strike_df: DataFrame with strike-level option data
            spot: Current spot price
            
        Returns:
            Dictionary of aggregated features
        """
        if strike_df.empty:
            return {}
        
        features = {}
        
        # Basic counts
        features['num_strikes'] = len(strike_df)
        
        # Total OI
        features['total_call_oi'] = strike_df['ce_oi'].sum() if 'ce_oi' in strike_df.columns else 0
        features['total_put_oi'] = strike_df['pe_oi'].sum() if 'pe_oi' in strike_df.columns else 0
        features['pcr'] = calculate_pcr(features['total_call_oi'], features['total_put_oi'])
        
        # Top change in OI
        if 'ce_change_oi' in strike_df.columns:
            features['top_call_change_oi'] = strike_df['ce_change_oi'].max()
        if 'pe_change_oi' in strike_df.columns:
            features['top_put_change_oi'] = strike_df['pe_change_oi'].max()
        
        # Median IVs
        if 'ce_iv' in strike_df.columns:
            features['median_ce_iv'] = strike_df['ce_iv'].median()
        if 'pe_iv' in strike_df.columns:
            features['median_pe_iv'] = strike_df['pe_iv'].median()
        
        # Median volume
        if 'ce_volume' in strike_df.columns and 'pe_volume' in strike_df.columns:
            total_volume = strike_df['ce_volume'].fillna(0) + strike_df['pe_volume'].fillna(0)
            features['median_volume'] = total_volume.median()
        
        # Max OI strike
        if 'ce_oi' in strike_df.columns and 'pe_oi' in strike_df.columns:
            total_oi = strike_df['ce_oi'].fillna(0) + strike_df['pe_oi'].fillna(0)
            max_oi_idx = total_oi.idxmax()
            features['max_oi_strike'] = strike_df.loc[max_oi_idx, 'strike']
        
        # ATM strike
        features['atm_strike_proxy'] = get_atm_strike(spot, strike_df['strike'])
        features['atm_strike'] = features['atm_strike_proxy']
        
        # OI skew
        if 'ce_oi' in strike_df.columns and 'pe_oi' in strike_df.columns:
            oi_skew = (strike_df['ce_oi'] - strike_df['pe_oi']) / (strike_df['ce_oi'] + strike_df['pe_oi'] + 1e-6)
            features['oi_skew_mean'] = oi_skew.mean()
            features['oi_skew'] = features['oi_skew_mean']
        
        # Top strike OI percentage
        if 'ce_oi' in strike_df.columns and 'pe_oi' in strike_df.columns:
            total_oi = features['total_call_oi'] + features['total_put_oi']
            if total_oi > 0:
                max_oi = strike_df['ce_oi'].fillna(0) + strike_df['pe_oi'].fillna(0)
                features['top_strike_oi_pct'] = max_oi.max() / total_oi
        
        # Spot
        features['spot'] = spot
        features['spot_note'] = spot
        
        # Median IV (overall)
        if 'ce_iv' in strike_df.columns and 'pe_iv' in strike_df.columns:
            all_ivs = pd.concat([strike_df['ce_iv'], strike_df['pe_iv']]).dropna()
            features['median_iv'] = all_ivs.median() if not all_ivs.empty else None
        
        return features
    
    def predict(self, features: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """
        Make prediction using loaded model.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Prediction dictionary with probabilities and predicted class
        """
        if self.model is None or self.features is None:
            return None
        
        # Prepare feature vector
        feature_vector = []
        for feat in self.features:
            feature_vector.append(features.get(feat, 0))
        
        X = np.array([feature_vector])
        
        # Predict
        probabilities = self.model.predict(X)[0]
        predicted_class_idx = np.argmax(probabilities)
        
        result = {
            'probabilities': probabilities.tolist(),
            'predicted_class_idx': int(predicted_class_idx),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.label_encoder:
            result['predicted_class'] = self.label_encoder.inverse_transform([predicted_class_idx])[0]
        
        return result
    
    def fetch_and_predict(self, symbol: str = "NIFTY") -> Optional[Dict[str, Any]]:
        """
        Complete pipeline: fetch → aggregate → predict.
        
        Args:
            symbol: Option symbol to fetch
            
        Returns:
            Prediction result dictionary or None if pipeline fails
        """
        # Fetch
        raw_data = self.fetch_option_chain(symbol)
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
        features = self.aggregate_features(strike_df, spot)
        
        # Predict
        prediction = self.predict(features)
        
        if prediction:
            prediction['features'] = features
            prediction['spot'] = spot
            prediction['num_strikes'] = len(strike_df)
        
        return prediction


if __name__ == "__main__":
    predictor = OptionChainPredictor()
    result = predictor.fetch_and_predict("NIFTY")
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to fetch and predict")

