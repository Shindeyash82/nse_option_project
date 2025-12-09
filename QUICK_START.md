# Quick Start: Live Predictions & After-Hours Usage

## Current Status

✅ **Model files are present** - Your trained model is ready  
⚠️ **LightGBM compatibility issue** - Python 3.13 has issues with LightGBM on Windows

## Solutions for LightGBM Issue

**Option 1: Use Python 3.11 or 3.12 (Recommended)**
```bash
# Install Python 3.11 or 3.12, then:
pip install -r requirements.txt
```

**Option 2: Use Conda**
```bash
conda create -n nse_env python=3.11
conda activate nse_env
conda install -c conda-forge lightgbm
pip install -r requirements.txt
```

**Option 3: Use WSL (Windows Subsystem for Linux)**
- Install WSL, then use Linux Python environment

## How to Run Predictions

### During Market Hours (9:15 AM - 3:30 PM IST)

**Method 1: Simple Prediction Script**
```bash
python src/predict_live.py NIFTY
```

**Method 2: Real-time Dashboard (Best for Live Monitoring)**
```bash
streamlit run src/app_inmemory.py
```
Then open http://localhost:8501

**Method 3: API Server**
```bash
python src/api_server.py
```
Then access: http://localhost:8000/predict/NIFTY

**Method 4: Real-time Monitoring Loop**
```bash
python src/realtime_loop.py --interval 5 --max-snapshots 100
```

### After Market Hours (Current Situation)

Since the market is closed, you have these options:

**Option 1: Use Historical Data Dashboard**
```bash
streamlit run src/app.py
```
This reads from `data/processed/` and works anytime!

**Option 2: Collect Data for Next Day**
```bash
# Set up collector to run during market hours
python src/collector.py --interval 60
```

**Option 3: Test the System (will show market closed message)**
```bash
python src/predict_live.py NIFTY
# Will inform you that market is closed
```

## What Works Right Now (Even with LightGBM Issue)

✅ **Data Collection** - Can collect data during market hours
```bash
python src/collector.py --once
```

✅ **Historical Dashboard** - View collected data
```bash
streamlit run src/app.py
```

✅ **CSV Parsing** - Parse downloaded CSV files
```bash
python src/parse_csv.py data/raw/optionchain_20251209_1500.csv
```

## What Needs LightGBM Fixed

❌ **Live Predictions** - Requires LightGBM
❌ **Real-time Dashboard Predictions** - Requires LightGBM  
❌ **API Predictions** - Requires LightGBM

## Recommended Workflow

### Today (Market Closed)
1. ✅ Test setup: `python test_setup.py`
2. ✅ View historical data: `streamlit run src/app.py`
3. ✅ Review collected data in `data/processed/`

### Tomorrow (During Market Hours)
1. Fix LightGBM issue (use Python 3.11/3.12)
2. Run live predictions: `python src/predict_live.py NIFTY`
3. Use live dashboard: `streamlit run src/app_inmemory.py`
4. Collect data: `python src/collector.py --interval 60`

## Files Created for You

- `src/predict_live.py` - Simple prediction script with better error messages
- `test_setup.py` - Check your setup
- `USAGE_GUIDE.md` - Comprehensive usage guide
- `QUICK_START.md` - This file

## Next Steps

1. **Fix LightGBM** (choose one):
   - Install Python 3.11 or 3.12
   - Or use conda environment
   - Or use WSL

2. **During Market Hours**:
   ```bash
   python src/predict_live.py NIFTY
   ```

3. **For Continuous Monitoring**:
   ```bash
   streamlit run src/app_inmemory.py
   ```

4. **For Data Collection**:
   ```bash
   python src/collector.py --interval 60
   ```

## Need Help?

- Check `USAGE_GUIDE.md` for detailed instructions
- Check `README.md` for project overview
- Run `python test_setup.py` to verify setup



