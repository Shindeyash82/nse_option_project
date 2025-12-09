# Usage Guide: Live Predictions & After-Hours

## Quick Start for Live Predictions

### During Market Hours (9:15 AM - 3:30 PM IST)

**Option 1: Simple Prediction Script**
```bash
python src/predict_live.py NIFTY
```

**Option 2: Using fetch_predict directly**
```bash
python src/fetch_predict.py
```

**Option 3: Real-time Monitoring Loop**
```bash
python src/realtime_loop.py --symbol NIFTY --interval 5 --max-snapshots 100
```

**Option 4: Streamlit Dashboard (In-Memory)**
```bash
streamlit run src/app_inmemory.py
```
Then open http://localhost:8501 in your browser

**Option 5: API Server**
```bash
python src/api_server.py --host 0.0.0.0 --port 8000
```
Then access:
- http://localhost:8000/predict/NIFTY (GET request)
- Or use POST to http://localhost:8000/predict with JSON body

### After Market Hours

The system will attempt to fetch data but may fail if:
- Market is closed (NSE hours: 9:15 AM - 3:30 PM IST)
- NSE API is not accessible
- Network issues

**Solutions for After-Hours:**

1. **Use Historical Data**: If you have collected data during market hours, use the disk-backed dashboard:
   ```bash
   streamlit run src/app.py
   ```

2. **Collect Data During Market Hours**: Run the collector to save snapshots:
   ```bash
   python src/collector.py --once  # Single snapshot
   python src/collector.py --interval 60  # Continuous collection
   ```

3. **Check Market Status**: The prediction script will inform you if the market is closed.

## Common Commands

### Single Prediction
```bash
# Default (NIFTY)
python src/predict_live.py

# Specific symbol
python src/predict_live.py BANKNIFTY
python src/predict_live.py FINNIFTY
```

### Continuous Collection
```bash
# Collect every 60 seconds
python src/collector.py --interval 60

# Collect once and exit
python src/collector.py --once

# Specific symbol
python src/collector.py --symbol BANKNIFTY --interval 60
```

### Real-time Monitoring
```bash
# Monitor with 5-second intervals, keep last 100 snapshots
python src/realtime_loop.py --interval 5 --max-snapshots 100

# Run once
python src/realtime_loop.py --once
```

### Dashboards

**Live Dashboard (In-Memory)**
```bash
streamlit run src/app_inmemory.py
```
- Fetches data in real-time
- No disk writes
- Best for live market monitoring

**Historical Dashboard (Disk-Backed)**
```bash
streamlit run src/app.py
```
- Reads from data/processed/
- Best for analyzing collected data
- Works anytime (doesn't need live market)

### API Server
```bash
python src/api_server.py --host 0.0.0.0 --port 8000
```

**Endpoints:**
- `GET /predict/{symbol}` - Quick prediction
- `POST /predict` - Prediction with custom request
- `GET /health` - Health check
- `GET /features` - List model features

**Example API calls:**
```bash
# Using curl
curl http://localhost:8000/predict/NIFTY

# Using Python requests
import requests
response = requests.get("http://localhost:8000/predict/NIFTY")
print(response.json())
```

## Troubleshooting

### "Model not loaded" Error
- Ensure model files exist in `models/` directory:
  - `lgb_model_oversampled.txt`
  - `label_encoder_oversampled.joblib`
  - `features_oversampled.json`

### "Failed to fetch option chain" Error
- **Market Closed**: NSE hours are 9:15 AM - 3:30 PM IST
- **Network Issues**: Check internet connection
- **API Access**: NSE may temporarily restrict API access

### LightGBM Import Error (Python 3.13)
If you encounter LightGBM compatibility issues with Python 3.13:
1. Use Python 3.11 or 3.12 instead
2. Or install LightGBM from source
3. Or use conda: `conda install -c conda-forge lightgbm`

## Best Practices

1. **During Market Hours**: Use `app_inmemory.py` or `predict_live.py` for real-time predictions
2. **After Market Hours**: Use `app.py` to analyze collected historical data
3. **Data Collection**: Run `collector.py` continuously during market hours to build historical dataset
4. **Model Retraining**: After collecting sufficient data, retrain model with `trainer.py`

## Schedule Recommendations

**Market Hours (9:15 AM - 3:30 PM IST):**
- Run collector continuously: `python src/collector.py --interval 60`
- Use live dashboard: `streamlit run src/app_inmemory.py`
- Or run predictions on-demand: `python src/predict_live.py`

**After Market Hours:**
- Analyze collected data: `streamlit run src/app.py`
- Retrain model if needed: `python src/trainer.py`
- Review predictions and plan for next day

## Output Files

- Predictions are saved as JSON: `prediction_{SYMBOL}_{TIMESTAMP}.json`
- Collected snapshots: `data/processed/{SYMBOL}_{TIMESTAMP}.parquet`
- Model files: `models/lgb_model_oversampled.txt` (and related files)



