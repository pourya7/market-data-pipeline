"""Download Trigger page with interval selection."""

import streamlit as st
import asyncio
from datetime import date, timedelta
from pathlib import Path
import sys
from io import StringIO

from market_data.clients.yahoo import YahooFinanceClient
from market_data.cleaning.pipeline import DataCleaner
from market_data.storage import StorageManager, StorageConfig
from market_data.models import OHLCVDataset


# Interval options with descriptions and date restrictions
INTERVAL_OPTIONS = {
    "1m (1 Minute)": {"interval": "1m", "max_days": 7, "description": "Last 7 days only"},
    "5m (5 Minutes)": {"interval": "5m", "max_days": 60, "description": "Last 60 days only"},
    "15m (15 Minutes)": {"interval": "15m", "max_days": 60, "description": "Last 60 days only"},
    "30m (30 Minutes)": {"interval": "30m", "max_days": 60, "description": "Last 60 days only"},
    "1h (1 Hour)": {"interval": "1h", "max_days": 730, "description": "Last 2 years"},
    "1d (Daily)": {"interval": "1d", "max_days": None, "description": "No limit"},
    "1wk (Weekly)": {"interval": "1wk", "max_days": None, "description": "No limit"},
}


def render_download():
    """Render the download trigger page."""
    st.title("⬇️ Download Data")
    st.markdown("Fetch new data from Yahoo Finance and store it locally.")
    
    # Configuration
    col1, col2 = st.columns([2, 1])
    
    with col1:
        symbols_input = st.text_input(
            "Ticker Symbols",
            value="AAPL",
            placeholder="AAPL, MSFT, GOOG",
            help="Enter one or more ticker symbols, separated by commas",
        )
    
    with col2:
        data_path = st.text_input(
            "Data Directory",
            value="./data",
        )
    
    # Interval selection
    st.markdown("### ⏱️ Interval")
    
    selected_interval_label = st.selectbox(
        "Data Interval",
        options=list(INTERVAL_OPTIONS.keys()),
        index=5,  # Default to Daily
        help="Select the bar interval. Intraday data has date range restrictions.",
    )
    
    interval_info = INTERVAL_OPTIONS[selected_interval_label]
    interval = interval_info["interval"]
    max_days = interval_info["max_days"]
    
    # Show restriction warning for intraday
    if max_days is not None:
        st.info(f"⚠️ **{selected_interval_label}**: Yahoo Finance limits this to the last **{max_days} days** of data.")
    
    # Date range - defaults based on interval
    today = date.today()
    
    if max_days is not None:
        # For intraday, default to max allowed range
        default_start = today - timedelta(days=min(max_days - 1, 7))
        min_allowed_date = today - timedelta(days=max_days)
    else:
        # For daily+, default to current month
        default_start = today.replace(day=1)
        min_allowed_date = date(2000, 1, 1)
    
    st.markdown("### 📅 Date Range")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            min_value=min_allowed_date,
            max_value=today,
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=today,
            min_value=min_allowed_date,
            max_value=today,
        )
    
    # Validate date range for intraday
    if max_days is not None:
        days_requested = (end_date - start_date).days + 1
        if days_requested > max_days:
            st.error(f"❌ Date range exceeds {max_days} days limit for {interval} interval. Please reduce the range.")
            return
    
    # Options
    with st.expander("⚙️ Options"):
        clean_data = st.checkbox("Clean data (validation + gap filling)", value=True)
        append_mode = st.checkbox("Append to existing data", value=True)
    
    # Download button
    st.markdown("---")
    
    if st.button("🚀 Start Download", type="primary", use_container_width=True):
        symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
        
        if not symbols:
            st.error("Please enter at least one ticker symbol.")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        # Log capture
        logs = []
        
        def log(message: str):
            logs.append(message)
            with log_container:
                st.code("\n".join(logs[-20:]), language="text")
        
        # Run downloads
        total = len(symbols)
        success_count = 0
        error_count = 0
        
        for i, symbol in enumerate(symbols):
            progress = (i + 1) / total
            progress_bar.progress(progress)
            status_text.text(f"Processing {symbol}... ({i + 1}/{total})")
            
            try:
                log(f"[{symbol}] Starting download ({interval})...")
                
                # Fetch data
                client = YahooFinanceClient()
                
                # Run async in sync context
                bars = asyncio.run(
                    client.fetch_ohlcv(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval,
                    )
                )
                
                if not bars:
                    log(f"[{symbol}] ⚠️ No data returned")
                    error_count += 1
                    continue
                
                log(f"[{symbol}] Fetched {len(bars)} bars")
                
                # Convert to DataFrame
                dataset = OHLCVDataset(
                    symbol=symbol,
                    bars=bars,
                    provider="yahoo",
                )
                df = dataset.to_pandas()
                
                # Clean if requested (only for daily data)
                if clean_data and interval == "1d":
                    log(f"[{symbol}] Cleaning data...")
                    cleaner = DataCleaner()
                    df = cleaner.clean(df)
                    log(f"[{symbol}] Cleaned: {len(df)} rows")
                elif clean_data and interval != "1d":
                    log(f"[{symbol}] ℹ️ Skipping cleaning (intraday data)")
                
                # Store
                log(f"[{symbol}] Saving to storage...")
                storage = StorageManager(StorageConfig(base_path=data_path))
                mode = "append" if append_mode else "overwrite"
                storage.save(df, symbol, mode=mode)
                
                log(f"[{symbol}] ✅ Success!")
                success_count += 1
                
            except Exception as e:
                log(f"[{symbol}] ❌ Error: {e}")
                error_count += 1
        
        # Completion
        progress_bar.progress(1.0)
        status_text.empty()
        
        # Clear cache so dashboard can see new data
        st.cache_data.clear()
        
        # Summary
        st.markdown("---")
        if error_count == 0:
            st.success(f"✅ Downloaded {success_count} symbol(s) successfully!")
        else:
            st.warning(f"Completed with {success_count} success, {error_count} errors")
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 View Health Dashboard"):
                st.session_state["nav"] = "Health Dashboard"
                st.rerun()
        with col2:
            if st.button("📈 View Charts"):
                st.session_state["nav"] = "Charts"
                st.rerun()
