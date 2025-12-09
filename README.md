# NSE Option Chain Optimizer

A comprehensive system for collecting, analyzing, and predicting NSE (National Stock Exchange) option chain data using machine learning.

## Project Structure

```
nse-option-chain-optimizer/
├─ data/
│  ├─ raw/                         # (parquet) per-snapshot strike-level files (if persisting)
│  └─ processed/                   # aggregated snapshots and other processed files
├─ models/
│  ├─ lgb_model_oversampled.txt    # trained LightGBM model (example)
│  ├─ label_encoder_oversampled.joblib
│  └─ features_oversampled.json
├─ src/
│  ├─ collector.py                 # collector loop (fetch option-chain, parse, save agg) -- supports --once
│  ├─ fetch_predict.py             # in-memory fetch → aggregate → predict (no disk writes)
│  ├─ realtime_loop.py             # short-lived in-memory loop keeping last-N snapshots (deque)
│  ├─ trainer.py                   # script to train LightGBM on aggregated snapshots (retrain after data collected)
│  ├─ backtester.py                # option-level backtester (simulate buys, premiums, theta)
│  ├─ api_server.py                 # FastAPI app to expose /predict endpoints (optional)
│  ├─ app.py                       # Streamlit dashboard (disk-backed version: reads aggregated files)
│  ├─ app_inmemory.py              # Streamlit dashboard (in-memory live predictions using fetch_predict)
│  ├─ utils.py                     # shared helpers (parsing, numeric cleaning, timestamp helpers)
│  └─ parse_csv.py                 # CSV parser (parse NSE .csv downloads into strike DF) - optional
├─ requirements.txt                # pip install -r requirements.txt
├─ Dockerfile                      # optional: containerize collector + app
├─ docker-compose.yml              # optional: compose for collector + api + streamlit
├─ .env.example                    # environment var examples (NSE_BASE etc.)
├─ .vscode/
│  ├─ launch.json                  # debug configs for VS Code
│  └─ tasks.json                   # run Streamlit / collector tasks
├─ README.md                       # quickstart + commands for VS Code / Drive / remote server
└─ LICENSE
```

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nse_option_project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Usage

#### Data Collection

**Collect a single snapshot:**
```bash
python src/collector.py --once
```

**Run continuous collection:**
```bash
python src/collector.py --interval 60  # Collect every 60 seconds
```

**With custom symbol:**
```bash
python src/collector.py --symbol BANKNIFTY --once
```

#### Training Model

After collecting data, train the model:
```bash
python src/trainer.py --data-dir data/processed
```

#### Real-time Predictions

**Fetch and predict once:**
```bash
python src/fetch_predict.py
```

**Run real-time monitoring loop:**
```bash
python src/realtime_loop.py --interval 5 --max-snapshots 100
```

#### Dashboards

**Disk-backed dashboard (reads from data/processed):**
```bash
streamlit run src/app.py
```

**In-memory live dashboard:**
```bash
streamlit run src/app_inmemory.py
```

#### API Server

Start the FastAPI server:
```bash
python src/api_server.py --host 0.0.0.0 --port 8000
```

API endpoints:
- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Get prediction (with request body)
- `GET /predict/{symbol}` - Quick prediction
- `GET /features` - List model features

## VS Code Integration

### Debug Configurations

The project includes VS Code launch configurations in `.vscode/launch.json`:
- Collector (once)
- Collector (continuous)
- Fetch & Predict
- Real-time Loop
- Trainer
- API Server
- Streamlit App
- Streamlit App (In-memory)

### Tasks

Pre-configured tasks in `.vscode/tasks.json`:
- Collector: Run Once
- Collector: Run Continuous
- Fetch & Predict
- Real-time Loop
- Train Model
- Run API Server
- Run Streamlit App
- Run Streamlit App (In-memory)
- Install Dependencies

## Docker Deployment

### Build and Run

**Build image:**
```bash
docker build -t nse-option-optimizer .
```

**Run collector:**
```bash
docker run -v $(pwd)/data:/app/data -v $(pwd)/models:/app/models nse-option-optimizer python src/collector.py --once
```

### Docker Compose

Run all services (collector, API, Streamlit):
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

## Remote Server Setup

### On Google Drive / Cloud Storage

1. Mount your Drive/cloud storage
2. Set data directory paths in configuration
3. Run collector as a background service:
```bash
nohup python src/collector.py --interval 60 > collector.log 2>&1 &
```

### Systemd Service (Linux)

Create `/etc/systemd/system/nse-collector.service`:
```ini
[Unit]
Description=NSE Option Chain Collector
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/nse_option_project
ExecStart=/usr/bin/python3 src/collector.py --interval 60
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable nse-collector
sudo systemctl start nse-collector
```

## Development

### Code Structure

- **utils.py**: Shared utility functions for parsing and data cleaning
- **collector.py**: Data collection loop with disk persistence
- **fetch_predict.py**: In-memory prediction pipeline
- **realtime_loop.py**: Real-time monitoring with deque-based storage
- **trainer.py**: Model training script with SMOTE oversampling
- **backtester.py**: Option trading strategy backtesting
- **api_server.py**: REST API for predictions
- **app.py**: Streamlit dashboard (disk-backed)
- **app_inmemory.py**: Streamlit dashboard (in-memory)

### Adding New Features

1. Add feature extraction logic in `fetch_predict.py` → `aggregate_features()`
2. Update feature list in `models/features_oversampled.json` after retraining
3. Retrain model with `trainer.py`

## Requirements

See `requirements.txt` for full list. Key dependencies:
- pandas
- numpy
- lightgbm
- scikit-learn
- imbalanced-learn (for SMOTE)
- streamlit
- fastapi
- uvicorn
- requests
- plotly

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.



