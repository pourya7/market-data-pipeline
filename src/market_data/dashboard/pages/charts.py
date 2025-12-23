"""Interactive Charts page with technical indicators."""

import streamlit as st
from datetime import date, timedelta
from pathlib import Path

from market_data.storage import StorageManager, StorageConfig
from market_data.features import TechnicalAnalyzer
from market_data.dashboard.components.charts import (
    create_candlestick_chart,
    create_line_chart,
    create_indicator_chart,
)


def render_charts():
    """Render the interactive charts page."""
    st.title("📈 Interactive Charts")
    st.markdown("Visualize OHLCV data with interactive Plotly charts and technical indicators.")
    
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
    st.sidebar.markdown("### ⚙️ Chart Options")
    
    chart_type = st.sidebar.radio(
        "Chart Type",
        ["Candlestick", "Line"],
        horizontal=True,
    )
    
    show_volume = st.sidebar.checkbox("Show Volume", value=True)
    
    # Technical indicators
    st.sidebar.markdown("### 📊 Technical Indicators")
    
    # Moving Averages
    show_sma = st.sidebar.checkbox("SMA (20, 50)", value=False)
    show_ema = st.sidebar.checkbox("EMA (12, 26)", value=False)
    show_bbands = st.sidebar.checkbox("Bollinger Bands", value=False)
    
    # Momentum (separate panel)
    show_rsi = st.sidebar.checkbox("RSI (14)", value=False)
    show_macd = st.sidebar.checkbox("MACD", value=False)
    show_stoch = st.sidebar.checkbox("Stochastic", value=False)
    
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
    
    # Calculate indicators if needed
    analyzer = TechnicalAnalyzer()
    
    if show_sma:
        df = analyzer.add_sma(df, length=20)
        df = analyzer.add_sma(df, length=50)
    
    if show_ema:
        df = analyzer.add_ema(df, length=12)
        df = analyzer.add_ema(df, length=26)
    
    if show_bbands:
        df = analyzer.add_bbands(df, length=20, std=2.0)
    
    if show_rsi:
        df = analyzer.add_rsi(df, length=14)
    
    if show_macd:
        df = analyzer.add_macd(df)
    
    if show_stoch:
        df = analyzer.add_stochastic(df)
    
    # Display chart
    st.markdown(f"### {selected_symbol}")
    st.caption(f"{len(df):,} data points • {start_date} to {end_date}")
    
    # Build overlay indicators list
    overlays = []
    if show_sma:
        overlays.extend(["sma_20", "sma_50"])
    if show_ema:
        overlays.extend(["ema_12", "ema_26"])
    if show_bbands:
        overlays.extend(["bband_lower_20", "bband_mid_20", "bband_upper_20"])
    
    if chart_type == "Candlestick":
        fig = create_candlestick_chart(
            df,
            title=f"{selected_symbol} OHLCV",
            show_volume=show_volume,
            overlays=overlays,
        )
    else:
        fig = create_line_chart(
            df,
            column="close",
            title=f"{selected_symbol} Close Price",
            overlays=overlays,
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Momentum indicators (separate charts)
    if show_rsi:
        st.markdown("#### RSI (14)")
        fig_rsi = create_indicator_chart(df, "rsi_14", title="RSI", yaxis_range=[0, 100])
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    if show_macd:
        st.markdown("#### MACD")
        fig_macd = create_indicator_chart(
            df, 
            ["macd_12_26_9", "macd_signal_12_26_9"],
            title="MACD",
            histogram="macd_hist_12_26_9",
        )
        st.plotly_chart(fig_macd, use_container_width=True)
    
    if show_stoch:
        st.markdown("#### Stochastic")
        fig_stoch = create_indicator_chart(
            df,
            ["stoch_k_14", "stoch_d_14_3"],
            title="Stochastic",
            yaxis_range=[0, 100],
        )
        st.plotly_chart(fig_stoch, use_container_width=True)
    
    # Data table
    with st.expander("📋 View Raw Data"):
        # Format columns dynamically
        format_dict = {
            "open": "{:.2f}",
            "high": "{:.2f}",
            "low": "{:.2f}",
            "close": "{:.2f}",
            "volume": "{:,.0f}",
        }
        # Add formatting for indicator columns
        for col in df.columns:
            if col not in format_dict and col not in ["open", "high", "low", "close", "volume"]:
                format_dict[col] = "{:.2f}"
        
        st.dataframe(
            df.tail(50).style.format(format_dict, na_rep="-"),
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
        
        # Show indicator values
        if show_rsi and "rsi_14" in df.columns:
            rsi_val = df["rsi_14"].iloc[-1]
            if not pd.isna(rsi_val):
                st.metric("RSI (14)", f"{rsi_val:.1f}")


# Need to import pandas for NaN check
import pandas as pd
