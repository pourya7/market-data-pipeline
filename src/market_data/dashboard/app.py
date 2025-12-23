"""Main Streamlit dashboard application."""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Market Data Command Center",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main dashboard entry point."""
    # Sidebar navigation
    st.sidebar.title("📊 Command Center")
    
    pages = ["🏥 Health Dashboard", "📈 Charts", "⬇️ Download"]
    
    # Check for programmatic navigation from session state
    default_index = 0
    if "nav" in st.session_state:
        nav = st.session_state.pop("nav")
        if nav == "health":
            default_index = 0
        elif nav == "charts":
            default_index = 1
        elif nav == "download":
            default_index = 2
    
    page = st.sidebar.radio(
        "Navigation",
        pages,
        index=default_index,
        label_visibility="collapsed",
    )
    
    if page == "🏥 Health Dashboard":
        from market_data.dashboard.pages.health import render_health_dashboard
        render_health_dashboard()
    elif page == "📈 Charts":
        from market_data.dashboard.pages.charts import render_charts
        render_charts()
    elif page == "⬇️ Download":
        from market_data.dashboard.pages.download import render_download
        render_download()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Market Data Pipeline v0.1.0")


if __name__ == "__main__":
    main()
