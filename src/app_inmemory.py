"""
Streamlit dashboard using in-memory live predictions via fetch_predict.
No disk reads - fetches and predicts in real-time.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from src.fetch_predict import OptionChainPredictor
from src.realtime_loop import RealtimeMonitor


# Page config
st.set_page_config(
    page_title="NSE Option Chain Predictor (Live)",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'predictor' not in st.session_state:
    st.session_state.predictor = OptionChainPredictor()
    st.session_state.monitor = None
    st.session_state.predictions_history = []


def main():
    st.title("📈 NSE Option Chain Predictor - Live Dashboard")
    st.markdown("Real-time option chain analysis and predictions (in-memory)")
    
    # Sidebar
    st.sidebar.header("Configuration")
    symbol = st.sidebar.selectbox("Symbol", ["NIFTY", "BANKNIFTY", "FINNIFTY"], index=0)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Live Prediction", "Real-time Monitor", "About"])
    
    with tab1:
        st.header("Live Prediction")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Fetch & Predict", type="primary"):
                with st.spinner("Fetching option chain and predicting..."):
                    result = st.session_state.predictor.fetch_and_predict(symbol)
                    
                    if result:
                        st.session_state.predictions_history.append({
                            'timestamp': datetime.now(),
                            'symbol': symbol,
                            **result
                        })
                        
                        st.success("Prediction successful!")
                        
                        # Display prediction
                        st.subheader("Prediction Result")
                        if result.get('predicted_class'):
                            st.metric("Predicted Class", result['predicted_class'])
                        else:
                            st.metric("Predicted Class Index", result.get('predicted_class_idx', 'N/A'))
                        
                        # Probabilities
                        if result.get('probabilities'):
                            prob_df = pd.DataFrame({
                                'Class': range(len(result['probabilities'])),
                                'Probability': result['probabilities']
                            })
                            fig = px.bar(prob_df, x='Class', y='Probability', 
                                       title="Prediction Probabilities")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Spot price
                        if result.get('spot'):
                            st.metric("Spot Price", f"₹{result['spot']:.2f}")
                    else:
                        st.error("Failed to fetch option chain or make prediction")
        
        with col2:
            st.subheader("Recent Predictions")
            if st.session_state.predictions_history:
                history_df = pd.DataFrame(st.session_state.predictions_history)
                st.dataframe(
                    history_df[['timestamp', 'symbol', 'predicted_class_idx', 'spot']].tail(10),
                    use_container_width=True
                )
            else:
                st.info("No predictions yet. Click 'Fetch & Predict' to start.")
        
        # Features display
        if st.session_state.predictions_history:
            st.subheader("Latest Features")
            latest = st.session_state.predictions_history[-1]
            if latest.get('features'):
                features_df = pd.DataFrame([latest['features']]).T
                features_df.columns = ['Value']
                st.dataframe(features_df, use_container_width=True)
    
    with tab2:
        st.header("Real-time Monitor")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            interval = st.number_input("Fetch Interval (seconds)", min_value=1, value=5, step=1)
        with col2:
            max_snapshots = st.number_input("Max Snapshots", min_value=10, value=100, step=10)
        with col3:
            duration = st.number_input("Duration (seconds)", min_value=0, value=0, step=60,
                                      help="0 = run indefinitely")
        
        col_start, col_stop = st.columns(2)
        
        with col_start:
            if st.button("Start Monitor", type="primary"):
                if st.session_state.monitor is None or not st.session_state.monitor.running:
                    st.session_state.monitor = RealtimeMonitor(
                        max_snapshots=max_snapshots,
                        symbol=symbol,
                        interval=interval
                    )
                    st.success("Monitor started!")
                else:
                    st.warning("Monitor already running")
        
        with col_stop:
            if st.button("Stop Monitor"):
                if st.session_state.monitor and st.session_state.monitor.running:
                    st.session_state.monitor.stop()
                    st.success("Monitor stopped!")
                else:
                    st.info("Monitor not running")
        
        # Display monitor status
        if st.session_state.monitor:
            stats = st.session_state.monitor.get_statistics()
            if stats:
                st.subheader("Monitor Statistics")
                st.json(stats)
                
                # Display recent snapshots
                recent = st.session_state.monitor.get_recent(20)
                if recent:
                    st.subheader("Recent Snapshots")
                    snapshot_df = pd.DataFrame([
                        {
                            'timestamp': s.get('timestamp'),
                            'predicted_class': s.get('predicted_class', s.get('predicted_class_idx')),
                            'spot': s.get('spot')
                        }
                        for s in recent
                    ])
                    st.dataframe(snapshot_df, use_container_width=True)
                    
                    # Plot spot over time
                    if 'spot' in snapshot_df.columns:
                        fig = px.line(snapshot_df, x='timestamp', y='spot', 
                                     title="Spot Price Over Time")
                        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("About")
        st.markdown("""
        ### NSE Option Chain Predictor - Live Dashboard
        
        This dashboard provides real-time option chain analysis and predictions using
        in-memory processing. No disk writes are performed - all data is fetched and
        processed on-the-fly.
        
        **Features:**
        - Live option chain fetching
        - Real-time predictions using trained LightGBM model
        - Real-time monitoring with configurable intervals
        - Historical prediction tracking
        
        **Usage:**
        1. Select a symbol (NIFTY, BANKNIFTY, FINNIFTY)
        2. Click "Fetch & Predict" for one-time prediction
        3. Use "Real-time Monitor" tab for continuous monitoring
        """)


if __name__ == "__main__":
    main()



