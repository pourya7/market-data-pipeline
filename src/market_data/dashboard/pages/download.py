"""Download Trigger page."""

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
    
    # Date range - defaults to current month
    today = date.today()
    month_start = today.replace(day=1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=month_start,
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=today,
        )
    
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
                log(f"[{symbol}] Starting download...")
                
                # Fetch data
                client = YahooFinanceClient()
                
                # Run async in sync context
                bars = asyncio.run(
                    client.fetch_ohlcv(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
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
                
                # Clean if requested
                if clean_data:
                    log(f"[{symbol}] Cleaning data...")
                    cleaner = DataCleaner()
                    df = cleaner.clean(df)
                    log(f"[{symbol}] Cleaned: {len(df)} rows")
                
                # Store
                log(f"[{symbol}] Saving to storage...")
                storage = StorageManager(StorageConfig(base_path=data_path))
                mode = "append" if append_mode else "overwrite"
                storage.save(df, symbol, mode=mode)
                
                log(f"[{symbol}] ✅ Success!")
                success_count += 1
                
            except Exception as e:
                log(f"[{symbol}] ❌ Error: {str(e)}")
                error_count += 1
        
        # Final status
        progress_bar.progress(1.0)
        status_text.empty()
        
        if error_count == 0:
            st.success(f"✅ Successfully downloaded {success_count} symbol(s)!")
        elif success_count > 0:
            st.warning(f"⚠️ Completed: {success_count} success, {error_count} failed")
        else:
            st.error(f"❌ All {error_count} downloads failed")
        
        # Clear any cached data
        st.cache_data.clear()
        
        # Offer to navigate to other pages
        st.info("💡 Data saved! Navigate to Health Dashboard or Charts to view.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏥 Go to Health Dashboard", use_container_width=True):
                st.session_state["nav"] = "health"
                st.rerun()
        with col2:
            if st.button("📈 Go to Charts", use_container_width=True):
                st.session_state["nav"] = "charts"
                st.rerun()
