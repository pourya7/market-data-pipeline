"""Health Dashboard page."""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from market_data.storage import StorageManager, StorageConfig
from market_data.dashboard.components.status import get_status_emoji


def render_health_dashboard():
    """Render the health dashboard page."""
    st.title("🏥 Health Dashboard")
    st.markdown("Monitor the health and status of your market data.")
    
    # Storage configuration
    col1, col2 = st.columns([3, 1])
    with col1:
        data_path = st.text_input(
            "Data Directory",
            value="./data",
            help="Path to your data storage directory",
        )
    with col2:
        st.write("")  # Spacing
        st.write("")
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Load storage manager
    try:
        storage = StorageManager(StorageConfig(base_path=data_path))
        storage.reload_manifest()  # Force reload for fresh data
        symbols = storage.get_available_symbols()
    except Exception as e:
        st.error(f"Failed to load storage: {e}")
        st.info("💡 Make sure the data directory exists and contains valid parquet files.")
        return
    
    if not symbols:
        st.warning("No data found in storage.")
        st.info("💡 Use the Download page to fetch data for your tickers.")
        return
    
    # Build health table
    st.markdown("### 📋 Ticker Inventory")
    
    health_data = []
    
    for symbol in symbols:
        try:
            # Get partition info
            partitions = storage.partitions.get_partitions_for_symbol(symbol)
            years = [p.year for p in partitions]
            
            # Load manifest info
            ticker_info = storage.manifest.tickers.get(symbol)
            
            if ticker_info:
                last_updated = datetime.fromisoformat(ticker_info.last_updated)
                
                # Get date range from all partitions
                all_start_dates = []
                all_end_dates = []
                total_rows = 0
                
                for year_str, pm in ticker_info.partitions.items():
                    all_start_dates.append(pm.start_date)
                    all_end_dates.append(pm.end_date)
                    total_rows += pm.rows
                
                start_date = min(all_start_dates) if all_start_dates else "N/A"
                end_date = max(all_end_dates) if all_end_dates else "N/A"
            else:
                last_updated = None
                start_date = "N/A"
                end_date = "N/A"
                total_rows = 0
            
            # Determine status
            emoji, status = get_status_emoji(last_updated)
            
            health_data.append({
                "Status": f"{emoji}",
                "Symbol": symbol,
                "Start Date": start_date,
                "End Date": end_date,
                "Rows": total_rows,
                "Years": ", ".join(map(str, sorted(years))),
                "Health": status,
            })
        except Exception as e:
            health_data.append({
                "Status": "🔴",
                "Symbol": symbol,
                "Start Date": "Error",
                "End Date": str(e)[:30],
                "Rows": 0,
                "Years": "",
                "Health": "ERROR",
            })
    
    # Display table
    df = pd.DataFrame(health_data)
    
    # Color-coded styling
    def style_status(val):
        if "🟢" in str(val):
            return "background-color: #28a74520"
        elif "🟡" in str(val):
            return "background-color: #ffc10720"
        elif "🔴" in str(val):
            return "background-color: #dc354520"
        return ""
    
    styled_df = df.style.applymap(style_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
    
    # Summary stats
    st.markdown("### 📊 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Symbols", len(symbols))
    
    with col2:
        ok_count = sum(1 for row in health_data if row["Health"] == "OK")
        st.metric("Healthy", ok_count, delta=None)
    
    with col3:
        stale_count = sum(1 for row in health_data if "STALE" in row["Health"])
        st.metric("Stale", stale_count, delta=None if stale_count == 0 else f"-{stale_count}")
    
    with col4:
        total_rows = sum(row["Rows"] for row in health_data)
        st.metric("Total Rows", f"{total_rows:,}")
    
    # Storage stats
    stats = storage.get_storage_stats()
    st.markdown("### 💾 Storage")
    st.caption(f"Path: `{stats['base_path']}` • {stats['num_partitions']} partitions • {stats['total_size_mb']} MB")
