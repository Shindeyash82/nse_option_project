"""
Enhanced Streamlit Dashboard for NSE Option Chain Predictor
Modern UI with comprehensive features and visualizations.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.fetch_predict import OptionChainPredictor
from src.realtime_loop import RealtimeMonitor

# Page config
st.set_page_config(
    page_title="NSE Option Chain Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .prediction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'predictor' not in st.session_state:
    with st.spinner("Loading model..."):
        st.session_state.predictor = OptionChainPredictor()
    st.session_state.monitor = None
    st.session_state.predictions_history = []
    st.session_state.auto_refresh = False
    st.session_state.refresh_interval = 30


def format_number(value):
    """Format large numbers with K, M suffixes."""
    if value is None or pd.isna(value):
        return "N/A"
    if value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    elif value >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:.2f}"


def create_prediction_card(result):
    """Create a styled prediction card."""
    predicted_class = result.get('predicted_class', f"Class {result.get('predicted_class_idx', 'N/A')}")
    spot = result.get('spot', 0)
    timestamp = result.get('timestamp', datetime.now().isoformat())
    
    card_html = f"""
    <div class="prediction-box">
        <h2 style="margin: 0; font-size: 2rem;">{predicted_class}</h2>
        <p style="margin: 0.5rem 0; font-size: 1.2rem;">Spot: ₹{spot:.2f}</p>
        <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{timestamp}</p>
    </div>
    """
    return card_html


def main():
    # Header
    st.markdown('<div class="main-header">📈 NSE Option Chain Predictor</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        symbol = st.selectbox(
            "Select Symbol",
            ["NIFTY", "BANKNIFTY", "FINNIFTY"],
            index=0,
            help="Choose the option chain symbol"
        )
        
        st.divider()
        
        st.subheader("🔄 Auto Refresh")
        auto_refresh = st.checkbox(
            "Enable Auto Refresh",
            value=st.session_state.auto_refresh,
            help="Automatically fetch new predictions"
        )
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh Interval (seconds)",
                min_value=5,
                max_value=300,
                value=st.session_state.refresh_interval,
                step=5
            )
            st.session_state.refresh_interval = refresh_interval
        
        st.divider()
        
        st.subheader("ℹ️ Market Status")
        now = datetime.now().time()
        market_open = datetime.strptime("09:15", "%H:%M").time()
        market_close = datetime.strptime("15:30", "%H:%M").time()
        
        if market_open <= now <= market_close:
            st.success("🟢 Market OPEN")
            st.caption(f"Closes at 3:30 PM IST")
        else:
            st.warning("🔴 Market CLOSED")
            if now < market_open:
                st.caption(f"Opens at 9:15 AM IST")
            else:
                st.caption(f"Opens tomorrow at 9:15 AM IST")
        
        st.divider()
        
        st.subheader("📊 Quick Stats")
        if st.session_state.predictions_history:
            st.metric("Total Predictions", len(st.session_state.predictions_history))
            latest = st.session_state.predictions_history[-1]
            if latest.get('spot'):
                st.metric("Latest Spot", f"₹{latest['spot']:.2f}")
        else:
            st.info("No predictions yet")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Live Prediction", "📈 Analytics", "🔄 Real-time Monitor", "📚 About"])
    
    with tab1:
        st.header("Live Prediction & Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            col_fetch, col_clear = st.columns([3, 1])
            
            with col_fetch:
                if st.button("🔄 Fetch & Predict", type="primary", use_container_width=True):
                    with st.spinner("Fetching option chain data and making prediction..."):
                        result = st.session_state.predictor.fetch_and_predict(symbol)
                        
                        if result:
                            result['timestamp'] = datetime.now()
                            result['symbol'] = symbol
                            st.session_state.predictions_history.append(result)
                            st.success("✅ Prediction successful!")
                        else:
                            st.error("❌ Failed to fetch data. Market may be closed or API unavailable.")
            
            with col_clear:
                if st.button("🗑️ Clear History", use_container_width=True):
                    st.session_state.predictions_history = []
                    st.rerun()
        
        with col2:
            if st.session_state.predictions_history:
                latest = st.session_state.predictions_history[-1]
                st.markdown(create_prediction_card(latest), unsafe_allow_html=True)
        
        # Display latest prediction details
        if st.session_state.predictions_history:
            latest = st.session_state.predictions_history[-1]
            
            st.subheader("📊 Prediction Details")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if latest.get('spot'):
                    st.metric("Spot Price", f"₹{latest['spot']:.2f}")
            
            with col2:
                if latest.get('features', {}).get('pcr'):
                    pcr = latest['features']['pcr']
                    st.metric("PCR", f"{pcr:.2f}")
            
            with col3:
                if latest.get('features', {}).get('total_call_oi'):
                    st.metric("Call OI", format_number(latest['features']['total_call_oi']))
            
            with col4:
                if latest.get('features', {}).get('total_put_oi'):
                    st.metric("Put OI", format_number(latest['features']['total_put_oi']))
            
            # Probabilities chart
            if latest.get('probabilities'):
                st.subheader("🎲 Prediction Probabilities")
                prob_df = pd.DataFrame({
                    'Class': [f"Class {i}" for i in range(len(latest['probabilities']))],
                    'Probability': latest['probabilities']
                })
                
                fig = px.bar(
                    prob_df,
                    x='Class',
                    y='Probability',
                    title="Class Probabilities",
                    color='Probability',
                    color_continuous_scale='Blues',
                    text='Probability'
                )
                fig.update_traces(texttemplate='%{text:.2%}', textposition='outside')
                fig.update_layout(
                    yaxis_title="Probability",
                    xaxis_title="Predicted Class",
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Features table
            if latest.get('features'):
                st.subheader("🔍 Feature Values")
                features = latest['features']
                key_features = {
                    'Spot Price': features.get('spot'),
                    'PCR': features.get('pcr'),
                    'ATM Strike': features.get('atm_strike'),
                    'Max OI Strike': features.get('max_oi_strike'),
                    'Total Call OI': features.get('total_call_oi'),
                    'Total Put OI': features.get('total_put_oi'),
                    'Median CE IV': features.get('median_ce_iv'),
                    'Median PE IV': features.get('median_pe_iv'),
                    'Median Volume': features.get('median_volume'),
                    'OI Skew': features.get('oi_skew_mean'),
                }
                
                features_df = pd.DataFrame([
                    {'Feature': k, 'Value': v if v is not None else 'N/A'}
                    for k, v in key_features.items()
                ])
                st.dataframe(features_df, use_container_width=True, hide_index=True)
        
        else:
            st.info("👆 Click 'Fetch & Predict' to get your first prediction")
        
        # Auto-refresh logic
        if st.session_state.auto_refresh and st.session_state.predictions_history:
            time.sleep(st.session_state.refresh_interval)
            st.rerun()
    
    with tab2:
        st.header("📈 Analytics & History")
        
        if not st.session_state.predictions_history:
            st.info("No prediction history available. Make some predictions first!")
        else:
            history_df = pd.DataFrame(st.session_state.predictions_history)
            
            # Summary statistics
            st.subheader("📊 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Predictions", len(history_df))
            
            with col2:
                if 'spot' in history_df.columns:
                    st.metric("Avg Spot", f"₹{history_df['spot'].mean():.2f}")
            
            with col3:
                if 'spot' in history_df.columns:
                    st.metric("Min Spot", f"₹{history_df['spot'].min():.2f}")
            
            with col4:
                if 'spot' in history_df.columns:
                    st.metric("Max Spot", f"₹{history_df['spot'].max():.2f}")
            
            # Time series charts
            if 'timestamp' in history_df.columns and 'spot' in history_df.columns:
                st.subheader("📉 Spot Price Over Time")
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                history_df_sorted = history_df.sort_values('timestamp')
                
                fig = px.line(
                    history_df_sorted,
                    x='timestamp',
                    y='spot',
                    title="Spot Price Trend",
                    markers=True
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Prediction distribution
            if 'predicted_class_idx' in history_df.columns:
                st.subheader("📊 Prediction Distribution")
                pred_counts = history_df['predicted_class_idx'].value_counts().sort_index()
                
                fig = px.pie(
                    values=pred_counts.values,
                    names=[f"Class {i}" for i in pred_counts.index],
                    title="Prediction Class Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent predictions table
            st.subheader("📋 Recent Predictions")
            display_cols = ['timestamp', 'symbol', 'predicted_class_idx', 'spot']
            available_cols = [col for col in display_cols if col in history_df.columns]
            
            if available_cols:
                st.dataframe(
                    history_df[available_cols].tail(20).sort_values('timestamp', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
    
    with tab3:
        st.header("🔄 Real-time Monitoring")
        
        st.info("💡 Use this feature to continuously monitor option chain data during market hours")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            interval = st.number_input(
                "Fetch Interval (seconds)",
                min_value=1,
                max_value=300,
                value=5,
                step=1,
                help="How often to fetch new data"
            )
        
        with col2:
            max_snapshots = st.number_input(
                "Max Snapshots",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                help="Maximum number of snapshots to keep in memory"
            )
        
        with col3:
            duration = st.number_input(
                "Duration (seconds)",
                min_value=0,
                max_value=3600,
                value=0,
                step=60,
                help="0 = run indefinitely"
            )
        
        col_start, col_stop, col_status = st.columns([1, 1, 2])
        
        with col_start:
            if st.button("▶️ Start Monitor", type="primary", use_container_width=True):
                if st.session_state.monitor is None or not st.session_state.monitor.running:
                    st.session_state.monitor = RealtimeMonitor(
                        max_snapshots=max_snapshots,
                        symbol=symbol,
                        interval=interval
                    )
                    st.success("Monitor started!")
                    st.rerun()
                else:
                    st.warning("Monitor already running")
        
        with col_stop:
            if st.button("⏹️ Stop Monitor", use_container_width=True):
                if st.session_state.monitor and st.session_state.monitor.running:
                    st.session_state.monitor.stop()
                    st.success("Monitor stopped!")
                    st.rerun()
                else:
                    st.info("Monitor not running")
        
        # Display monitor status
        if st.session_state.monitor:
            stats = st.session_state.monitor.get_statistics()
            if stats:
                st.subheader("📊 Monitor Statistics")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Snapshots", stats.get('total_snapshots', 0))
                with col2:
                    if stats.get('spot_mean'):
                        st.metric("Avg Spot", f"₹{stats['spot_mean']:.2f}")
                with col3:
                    if stats.get('spot_min') and stats.get('spot_max'):
                        st.metric("Spot Range", f"₹{stats['spot_min']:.2f} - ₹{stats['spot_max']:.2f}")
                
                # Recent snapshots
                recent = st.session_state.monitor.get_recent(20)
                if recent:
                    st.subheader("📋 Recent Snapshots")
                    snapshot_df = pd.DataFrame([
                        {
                            'Timestamp': s.get('timestamp'),
                            'Predicted Class': s.get('predicted_class', s.get('predicted_class_idx')),
                            'Spot': f"₹{s.get('spot', 0):.2f}" if s.get('spot') else 'N/A'
                        }
                        for s in recent
                    ])
                    st.dataframe(snapshot_df, use_container_width=True, hide_index=True)
                    
                    # Plot spot over time
                    if any(s.get('spot') for s in recent):
                        spots = [s.get('spot') for s in recent if s.get('spot')]
                        timestamps = [s.get('timestamp') for s in recent if s.get('spot')]
                        
                        fig = px.line(
                            x=timestamps,
                            y=spots,
                            title="Spot Price Over Time (Monitor)",
                            labels={'x': 'Time', 'y': 'Spot Price (₹)'},
                            markers=True
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("📚 About")
        
        st.markdown("""
        ### NSE Option Chain Predictor - Enhanced Dashboard
        
        A comprehensive dashboard for real-time NSE option chain analysis and predictions.
        
        #### 🎯 Features
        
        - **Live Predictions**: Real-time option chain data fetching and ML-based predictions
        - **Auto Refresh**: Automatically update predictions at configurable intervals
        - **Analytics**: Historical analysis and trend visualization
        - **Real-time Monitoring**: Continuous monitoring with configurable parameters
        - **Multiple Symbols**: Support for NIFTY, BANKNIFTY, and FINNIFTY
        
        #### 📊 Prediction Model
        
        - **Algorithm**: LightGBM (Gradient Boosting)
        - **Features**: PCR, OI, IV, Volume, and more
        - **Training**: Trained on historical aggregated snapshots
        
        #### 🕐 Market Hours
        
        - **Open**: 9:15 AM IST
        - **Close**: 3:30 PM IST
        - **Note**: Predictions work best during market hours
        
        #### 💡 Usage Tips
        
        1. Select your symbol from the sidebar
        2. Click "Fetch & Predict" for instant predictions
        3. Enable "Auto Refresh" for continuous updates
        4. Use "Real-time Monitor" for extended monitoring sessions
        5. Check "Analytics" tab for historical insights
        
        #### 🔧 Technical Details
        
        - **Framework**: Streamlit
        - **Visualization**: Plotly
        - **ML Model**: LightGBM
        - **Data Source**: NSE India API
        
        ---
        
        **Version**: 1.0.0  
        **Last Updated**: December 2025
        """)


if __name__ == "__main__":
    main()

