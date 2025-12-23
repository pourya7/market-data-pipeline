"""Interactive Charts page."""

import streamlit as st
from datetime import date, timedelta
from pathlib import Path

from market_data.storage import StorageManager, StorageConfig
from market_data.dashboard.components.charts import create_candlestick_chart, create_line_chart


def render_charts():
    """Render the interactive charts page."""
    st.title("📈 Interactive Charts")
    st.markdown("Visualize OHLCV data with interactive Plotly charts.")
    
    # Storage configuration
    data_path = st.sidebar.text_input(
        "Data Directory",
        value="./data",
        key="charts_data_path",
    )
    
    # Load storage
    try:
        storage = StorageManager(StorageConfig(base_path=data_path))
        storage.reload_manifest()  # Force reload for fresh data
        symbols = storage.get_available_symbols()
    except Exception as e:
        st.error(f"Failed to load storage: {e}")
        return
    
    if not symbols:
        st.warning("No data found. Use the Download page to fetch data first.")
        return
    
    # Ticker selection
    st.sidebar.markdown("### 📌 Selection")
    
    selected_symbol = st.sidebar.selectbox(
        "Ticker Symbol",
        options=symbols,
        index=0,
    )
    
    # Date range
    available_years = storage.get_available_years(selected_symbol)
    
    if not available_years:
        st.warning(f"No data available for {selected_symbol}")
        return
    
    min_year = min(available_years)
    max_year = max(available_years)
    
    default_start = date(max_year, 1, 1)
    default_end = date.today()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=date(min_year, 1, 1),
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=default_end,
        )
    
    # Chart options
    st.sidebar.markdown("### ⚙️ Options")
    
    chart_type = st.sidebar.radio(
        "Chart Type",
        ["Candlestick", "Line"],
        horizontal=True,
    )
    
    show_volume = st.sidebar.checkbox("Show Volume", value=True)
    
    # Load data
    try:
        df = storage.load(
            selected_symbol,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return
    
    if df.empty:
        st.warning(f"No data found for {selected_symbol} in the selected date range.")
        return
    
    # Display chart
    st.markdown(f"### {selected_symbol}")
    st.caption(f"{len(df):,} data points • {start_date} to {end_date}")
    
    if chart_type == "Candlestick":
        fig = create_candlestick_chart(
            df,
            title=f"{selected_symbol} OHLCV",
            show_volume=show_volume,
        )
    else:
        fig = create_line_chart(
            df,
            column="close",
            title=f"{selected_symbol} Close Price",
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    with st.expander("📋 View Raw Data"):
        st.dataframe(
            df.tail(50).style.format({
                "open": "{:.2f}",
                "high": "{:.2f}",
                "low": "{:.2f}",
                "close": "{:.2f}",
                "volume": "{:,.0f}",
            }),
            use_container_width=True,
        )
    
    # Statistics
    with st.expander("📊 Statistics"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Open", f"${df['open'].iloc[-1]:.2f}")
        with col2:
            st.metric("High", f"${df['high'].max():.2f}")
        with col3:
            st.metric("Low", f"${df['low'].min():.2f}")
        with col4:
            st.metric("Close", f"${df['close'].iloc[-1]:.2f}")
        
        # Returns
        if len(df) > 1:
            returns = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
            st.metric("Period Return", f"{returns:.2f}%", delta=f"{returns:.2f}%")
