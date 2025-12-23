"""Status indicator components."""

import streamlit as st
from datetime import datetime, date, timedelta
from typing import Optional


def get_status_emoji(
    last_updated: Optional[datetime],
    has_gaps: bool = False,
    stale_hours: int = 24,
) -> tuple[str, str]:
    """Get status emoji and label based on data health.
    
    Args:
        last_updated: When the data was last updated.
        has_gaps: Whether gaps were detected.
        stale_hours: Hours after which data is considered stale.
        
    Returns:
        Tuple of (emoji, status label).
    """
    if has_gaps:
        return "🔴", "GAPS"
    
    if last_updated is None:
        return "⚪", "NO DATA"
    
    now = datetime.now()
    age = now - last_updated
    
    if age > timedelta(hours=stale_hours * 7):
        return "🔴", "VERY STALE"
    elif age > timedelta(hours=stale_hours):
        return "🟡", "STALE"
    else:
        return "🟢", "OK"


def render_status_badge(emoji: str, label: str) -> None:
    """Render a status badge.
    
    Args:
        emoji: Status emoji.
        label: Status label.
    """
    color_map = {
        "🟢": "#28a745",
        "🟡": "#ffc107", 
        "🔴": "#dc3545",
        "⚪": "#6c757d",
    }
    
    color = color_map.get(emoji, "#6c757d")
    
    st.markdown(
        f"""
        <span style="
            background-color: {color}20;
            color: {color};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        ">{emoji} {label}</span>
        """,
        unsafe_allow_html=True,
    )
