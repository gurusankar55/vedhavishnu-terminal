import streamlit as st
import requests
import pandas as pd
from modules.ui_layout import render_ui
from modules.early_pump import render_early_pump_scanner
from modules.breakout_scanner import render_breakout_scanner
from modules.advanced_scanner import apply_advanced_filters

st.set_page_config(
    page_title="VedhaVishnu Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="auto"
)

render_ui()

@st.cache_data(ttl=30)
def get_market_overview():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
                df = df[df['symbol'].str.endswith('USDT')].copy()
                for col in ['lastPrice', 'volume', 'quoteVolume', 'priceChangePercent']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
    except Exception as e:
        st.error(f"Error: {e}")
    return pd.DataFrame()

st.sidebar.markdown("<h2 style='color: #00F0FF; font-size: 20px;'>⚡ Navigation</h2>", unsafe_allow_html=True)
nav_choice = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Overview / Dashboard", 
        "🚀 Early Pump Scanner", 
        "⚡ Breakout & Whale Scanner"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📲 Telegram Alerts Setup")

if 'tg_token' not in st.session_state:
    st.session_state['tg_token'] = ""
if 'chat_id' not in st.session_state:
    st.session_state['chat_id'] = ""
if 'lock_credentials' not in st.session_state:
    st.session_state['lock_credentials'] = False

lock_state = st.sidebar.checkbox("🔒 Lock Telegram Credentials", value=st.session_state['lock_credentials'])
st.session_state['lock_credentials'] = lock_state

if lock_state:
    st.sidebar.success("Credentials locked securely!")
    tg_token = st.session_state['tg_token']
    chat_id = st.session_state['chat_id']
    st.sidebar.text_input("Telegram Bot Token", value="********************************", type="password", disabled=True)
    st.sidebar.text_input("Telegram Chat ID", value=chat_id, disabled=True)
else:
    tg_token = st.sidebar.text_input("Telegram Bot Token", value=st.session_state['tg_token'], type="password")
    chat_id = st.sidebar.text_input("Telegram Chat ID", value=st.session_state['chat_id'])
    st.session_state['tg_token'] = tg_token
    st.session_state['chat_id'] = chat_id

st.markdown("""
    <div style="text-align: center; margin-bottom: 20px; margin-top: 10px;">
        <h3 style="color: #00F0FF; letter-spacing: 2px; margin: 0;">⚡ VEDHAVISHNU</h3>
        <p style="color: #a7f3d0; font-size: 12px; margin: 2px 0 0 0;">Professional Binance Futures Quant Terminal</p>
    </div>
""", unsafe_allow_html=True)

if nav_choice == "🏠 Overview / Dashboard":
    df = get_market_overview()
    if not df.empty:
        tab1, tab2, tab3 = st.tabs(["🔥 Top Gainers", "📉 Top Losers", "💎 Top Volume"])
        with tab1:
            st.markdown("#### Top 10 Gainers (24h)")
            for _, row in df.sort_values(by='priceChangePercent', ascending=False).head(10).iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 10px;">
                        <span style="color: #00F0FF; font-weight: bold; font-size: 16px;">{row['symbol']}</span>
                        <span style="color: #e0f2f1; font-size: 15px;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #00FF88; font-weight: bold; font-size: 15px;">{row['priceChangePercent']:+.2f}%</span>
                    </div>
                """, unsafe_allow_html=True)
        with tab2:
            st.markdown("#### Top 10 Losers (24h)")
            for _, row in df.sort_values(by='priceChangePercent', ascending=True).head(10).iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 10px;">
                        <span style="color: #00F0FF; font-weight: bold; font-size: 16px;">{row['symbol']}</span>
                        <span style="color: #e0f2f1; font-size: 15px;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #FF4D4D; font-weight: bold; font-size: 15px;">{row['priceChangePercent']:+.2f}%</span>
                    </div>
                """, unsafe_allow_html=True)
        with tab3:
            st.markdown("#### Top 10 Volume Leaders (24h)")
            for _, row in df.sort_values(by='quoteVolume', ascending=False).head(10).iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 10px;">
                        <span style="color: #00F0FF; font-weight: bold; font-size: 16px;">{row['symbol']}</span>
                        <span style="color: #e0f2f1; font-size: 15px;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #00F0FF; font-size: 15px;">Vol: ${row['quoteVolume']:,.0f}</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("Fetching market overview data...")

elif nav_choice == "🚀 Early Pump Scanner":
    render_early_pump_scanner()

elif nav_choice == "⚡ Breakout & Whale Scanner":
    render_breakout_scanner()
    st.markdown("---")
    st.subheader("📲 Advanced Telegram & Volume Spike Trigger")
    if st.button("Run Advanced Whale & Telegram Filter"):
        market_df = get_market_overview()
        if not market_df.empty:
            with st.spinner("Analyzing Multi-Timeframe Volume Spikes & Sending Alerts..."):
                active_signals = apply_advanced_filters(market_df, tg_token, chat_id)
                if active_signals:
                    st.success(f"Successfully triggered alerts for: {active_signals}")
                else:
                    st.info("Scan completed. No major volume spikes matched the strict criteria right now.")