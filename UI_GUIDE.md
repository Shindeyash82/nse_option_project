# UI Dashboard Guide

## Available Dashboards

### 1. Enhanced Dashboard (Recommended) ⭐
**File**: `src/app_enhanced.py`

**Features**:
- 🎨 Modern, polished UI with custom styling
- 📊 Comprehensive analytics and visualizations
- 🔄 Auto-refresh capability
- 📈 Real-time monitoring
- 📋 Detailed feature displays
- 🎯 Prediction probability charts
- 📉 Historical trend analysis

**Run**:
```bash
streamlit run src/app_enhanced.py
```

### 2. Live Dashboard (In-Memory)
**File**: `src/app_inmemory.py`

**Features**:
- Real-time predictions
- In-memory processing (no disk writes)
- Basic monitoring

**Run**:
```bash
streamlit run src/app_inmemory.py
```

### 3. Historical Dashboard (Disk-Backed)
**File**: `src/app.py`

**Features**:
- View collected historical data
- Works anytime (doesn't need live market)
- Time series analysis
- Feature correlation

**Run**:
```bash
streamlit run src/app.py
```

## Quick Start

### Launch Enhanced Dashboard

1. **Open terminal** in project directory
2. **Run**:
   ```bash
   streamlit run src/app_enhanced.py
   ```
3. **Open browser** - Dashboard will open automatically at `http://localhost:8501`

### Using the Dashboard

#### 🎯 Live Prediction Tab
- Select symbol (NIFTY, BANKNIFTY, FINNIFTY) from sidebar
- Click "🔄 Fetch & Predict" button
- View prediction results, probabilities, and features
- Enable "Auto Refresh" for continuous updates

#### 📈 Analytics Tab
- View historical predictions
- See spot price trends over time
- Analyze prediction distribution
- Review recent predictions table

#### 🔄 Real-time Monitor Tab
- Configure monitoring parameters
- Start/stop continuous monitoring
- View real-time statistics
- Track spot price changes

#### 📚 About Tab
- Documentation and usage tips
- Feature overview
- Technical details

## Dashboard Features

### Sidebar Controls
- **Symbol Selection**: Choose NIFTY, BANKNIFTY, or FINNIFTY
- **Auto Refresh**: Enable automatic updates
- **Refresh Interval**: Set update frequency (5-300 seconds)
- **Market Status**: See if market is open/closed
- **Quick Stats**: View prediction statistics

### Main Features

1. **Live Predictions**
   - Real-time option chain data fetching
   - ML model predictions
   - Probability distributions
   - Key feature values

2. **Visualizations**
   - Spot price trends
   - Prediction probabilities (bar charts)
   - Prediction distribution (pie charts)
   - Time series analysis

3. **Analytics**
   - Summary statistics
   - Historical trends
   - Prediction patterns
   - Feature analysis

4. **Monitoring**
   - Continuous data collection
   - Real-time statistics
   - Snapshot history
   - Performance metrics

## Tips for Best Experience

1. **During Market Hours** (9:15 AM - 3:30 PM IST):
   - Use Enhanced Dashboard for live predictions
   - Enable Auto Refresh for continuous updates
   - Monitor real-time changes

2. **After Market Hours**:
   - Use Historical Dashboard to analyze collected data
   - Review past predictions and trends
   - Plan for next trading day

3. **Performance**:
   - Auto refresh interval: 30-60 seconds recommended
   - Monitor duration: Set based on your needs
   - Max snapshots: 100-200 for good balance

## Troubleshooting

### Dashboard won't start
- Check if Streamlit is installed: `pip install streamlit`
- Verify Python version: `python --version` (should be 3.10+)
- Check for port conflicts (default port: 8501)

### No predictions showing
- Ensure market is open (9:15 AM - 3:30 PM IST)
- Check internet connection
- Verify model files exist in `models/` directory

### Auto refresh not working
- Check if "Enable Auto Refresh" is checked in sidebar
- Verify refresh interval is set appropriately
- Refresh page if needed

## Keyboard Shortcuts

- `R` - Refresh data
- `C` - Clear cache
- `?` - Show keyboard shortcuts (in Streamlit)

## Browser Compatibility

- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ Internet Explorer (Not supported)

## Accessing Dashboard Remotely

If running on a remote server:

1. Start with host binding:
   ```bash
   streamlit run src/app_enhanced.py --server.address 0.0.0.0
   ```

2. Access via: `http://your-server-ip:8501`

3. Configure firewall to allow port 8501

## Next Steps

1. **Launch Enhanced Dashboard**: `streamlit run src/app_enhanced.py`
2. **Explore Features**: Try all tabs and features
3. **Enable Auto Refresh**: For continuous monitoring
4. **Check Analytics**: Review historical data
5. **Monitor Real-time**: Use during market hours

Enjoy your enhanced NSE Option Chain Predictor dashboard! 🚀

