"""
Streamlit dashboard (disk-backed version): reads aggregated files.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import glob


# Page config
st.set_page_config(
    page_title="NSE Option Chain Predictor",
    page_icon="📈",
    layout="wide"
)


def load_aggregated_data(data_dir: str = "data/processed") -> pd.DataFrame:
    """
    Load all aggregated snapshot files.
    
    Args:
        data_dir: Directory containing processed data files
        
    Returns:
        Combined DataFrame
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        return pd.DataFrame()
    
    # Load parquet files
    parquet_files = list(data_path.glob("*.parquet"))
    csv_files = list(data_path.glob("*.csv"))
    
    files = parquet_files if parquet_files else csv_files
    
    if not files:
        return pd.DataFrame()
    
    dfs = []
    for file in files:
        try:
            if file.suffix == '.parquet':
                df = pd.read_parquet(file)
            else:
                df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            st.warning(f"Error loading {file.name}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    data = pd.concat(dfs, ignore_index=True)
    
    # Ensure timestamp is datetime
    if 'timestamp' in data.columns:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.sort_values('timestamp').reset_index(drop=True)
    
    return data


def main():
    st.title("📈 NSE Option Chain Predictor Dashboard")
    st.markdown("Disk-backed version: reads aggregated snapshot files")
    
    # Sidebar
    st.sidebar.header("Configuration")
    data_dir = st.sidebar.text_input("Data Directory", value="data/processed")
    
    # Load data
    with st.spinner("Loading aggregated data..."):
        data = load_aggregated_data(data_dir)
    
    if data.empty:
        st.warning(f"No data found in {data_dir}. Run collector.py to collect data.")
        st.stop()
    
    st.success(f"Loaded {len(data)} snapshots")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Time Series", "Features", "Statistics"])
    
    with tab1:
        st.header("Data Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Snapshots", len(data))
        
        with col2:
            if 'timestamp' in data.columns:
                date_range = f"{data['timestamp'].min().date()} to {data['timestamp'].max().date()}"
                st.metric("Date Range", date_range)
        
        with col3:
            if 'symbol' in data.columns:
                symbols = data['symbol'].unique()
                st.metric("Symbols", ", ".join(symbols))
        
        with col4:
            if 'spot' in data.columns:
                latest_spot = data['spot'].iloc[-1] if len(data) > 0 else None
                st.metric("Latest Spot", f"₹{latest_spot:.2f}" if latest_spot else "N/A")
        
        # Display recent data
        st.subheader("Recent Snapshots")
        display_cols = ['timestamp', 'symbol', 'spot', 'pcr']
        available_cols = [col for col in display_cols if col in data.columns]
        st.dataframe(data[available_cols].tail(20), use_container_width=True)
    
    with tab2:
        st.header("Time Series Analysis")
        
        if 'timestamp' not in data.columns:
            st.warning("Timestamp column not found")
            st.stop()
        
        # Select metrics to plot
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()
        exclude_cols = ['predicted_class_idx']
        plot_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        selected_metrics = st.multiselect(
            "Select metrics to plot",
            plot_cols,
            default=['spot', 'pcr'] if 'spot' in plot_cols and 'pcr' in plot_cols else plot_cols[:2]
        )
        
        if selected_metrics:
            fig = go.Figure()
            
            for metric in selected_metrics:
                fig.add_trace(go.Scatter(
                    x=data['timestamp'],
                    y=data[metric],
                    mode='lines',
                    name=metric
                ))
            
            fig.update_layout(
                title="Time Series Plot",
                xaxis_title="Timestamp",
                yaxis_title="Value",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Feature Analysis")
        
        # Feature distribution
        numeric_cols = data.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        selected_feature = st.selectbox("Select feature", numeric_cols)
        
        if selected_feature:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Distribution")
                fig = px.histogram(data, x=selected_feature, nbins=50, title=f"{selected_feature} Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Statistics")
                stats = data[selected_feature].describe()
                st.dataframe(stats.to_frame().T, use_container_width=True)
                
                if 'timestamp' in data.columns:
                    fig = px.scatter(data, x='timestamp', y=selected_feature, 
                                   title=f"{selected_feature} Over Time")
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.header("Statistics")
        
        st.subheader("Summary Statistics")
        numeric_data = data.select_dtypes(include=['float64', 'int64'])
        st.dataframe(numeric_data.describe(), use_container_width=True)
        
        st.subheader("Correlation Matrix")
        if len(numeric_data.columns) > 1:
            corr = numeric_data.corr()
            fig = px.imshow(corr, text_auto=True, aspect="auto", title="Feature Correlation")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Missing Values")
        missing = data.isnull().sum()
        missing_df = missing[missing > 0].to_frame('Count')
        if not missing_df.empty:
            st.dataframe(missing_df, use_container_width=True)
        else:
            st.info("No missing values found")


if __name__ == "__main__":
    main()



