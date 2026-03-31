import time

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_connection


# 1. Manual Data Fetcher (No SQLAlchemy Warning)
def get_data(query, params=None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                # Fetch rows and column names manually
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()


# 2. Page Configuration
st.set_page_config(page_title="SentinelStock", layout="wide")
st.title("📈 SentinelStock: Real-Time Monitor")

# 3. Sidebar
tickers_df = get_data("SELECT ticker FROM stocks ORDER BY ticker ASC")
if not tickers_df.empty:
    selected_ticker = st.sidebar.selectbox("Select Ticker", tickers_df["ticker"])
else:
    st.stop()

refresh_rate = st.sidebar.slider("Refresh Rate", 5, 60, 10)

# 4. Main UI Logic
snap_query = """
    SELECT price, volume, captured_at FROM price_logs 
    WHERE ticker = %s ORDER BY captured_at DESC LIMIT 2
"""
snap_df = get_data(snap_query, (selected_ticker,))

if not snap_df.empty:
    # Metrics
    curr = float(snap_df.iloc[0]["price"])
    prev = float(snap_df.iloc[1]["price"]) if len(snap_df) > 1 else curr

    col1, col2 = st.columns(2)
    col1.metric("Price", f"${curr:,.2f}", f"{curr - prev:+.2f}")
    col2.metric("Sync Time", snap_df.iloc[0]["captured_at"].strftime("%H:%M:%S"))

    # Chart - Using 2026 'width="stretch"' standard
    hist_query = "SELECT captured_at, price FROM price_logs WHERE ticker = %s ORDER BY captured_at DESC LIMIT 100"
    hist_df = get_data(hist_query, (selected_ticker,))

    fig = px.line(hist_df, x="captured_at", y="price", template="plotly_dark")
    st.plotly_chart(fig, width="stretch", key="main_chart")

    # Table
    summary_df = get_data(
        "SELECT * FROM daily_summary WHERE ticker = %s", (selected_ticker,)
    )
    st.dataframe(summary_df, width="stretch")

# 5. Loop
time.sleep(refresh_rate)
st.rerun()
