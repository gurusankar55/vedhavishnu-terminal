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

# Render Global UI Styling
render_ui()

# Fetch Market data using Multi-Exchange Fallback (Binance -> Bybit -> MEXC)
@st.cache_data(ttl=60)
def get_market_overview():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Method 1: Binance Spot API
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df = df[df['symbol'].str.endswith('USDT')].copy()
                for col in ['lastPrice', 'volume', 'quoteVolume', 'priceChangePercent']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
    except Exception:
        pass

    # Method 2: Bybit Linear Ticker API (Extremely reliable for cloud servers)
    try:
        bybit_url = "https://api.bybit.com/v5/market/tickers?category=linear"
        res2 = requests.get(bybit_url, headers=headers, timeout=8)
        if res2.status_code == 200:
            result = res2.json().get('result', {}).get('list', [])
            if result:
                rows = []
                for item in result:
                    sym = item.get('symbol', '')
                    if sym.endswith('USDT'):
                        price = float(item.get('lastPrice', 0) or 0)
                        vol = float(item.get('volume24h', 0) or 0)
                        turnover = float(item.get('turnover24h', 0) or 0)
                        change = float(item.get('price24hPcnt', 0) or 0) * 100
                        rows.append({
                            'symbol': sym,
                            'lastPrice': price,
                            'volume': vol,
                            'quoteVolume': turnover if turnover > 0 else vol * price,
                            'priceChangePercent': change
                        })
                df = pd.DataFrame(rows)
                if not df.empty:
                    return df
    except Exception:
        pass

    # Method 3: MEXC Ticker API Fallback
    try:
        mexc_url = "https://api.mexc.com/api/v3/ticker/24hr"
        res3 = requests.get(mexc_url, headers=headers, timeout=8)
        if res3.status_code == 200:
            data = res3.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df = df[df['symbol'].str.endswith('USDT')].copy()
                for col in ['lastPrice', 'volume', 'quoteVolume', 'priceChangePercent']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                return df
    except Exception as e:
        st.error(f"All exchange data sources failed: {e}")

    return pd.DataFrame()

# Sidebar Navigation
st.sidebar.markdown("<h2 style='color: #00F0FF; font-size: 20px;'>⚡ Navigation</h2>", unsafe_allow_html=True)
nav_choice = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Overview / Dashboard", 
        "🚀 Early Pump Scanner", 
        "⚡ Breakout & Whale Scanner"
    ]
)

# Sidebar Telegram Config with Permanent Lock & Session State Persistence
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

# Clean small center title for VedhaVishnu
st.markdown("""
    <div style="text-align: center; margin-bottom: 20px; margin-top: 10px;">
        <h3 style="color: #00F0FF; letter-spacing: 2px; margin: 0;">⚡ VEDHAVISHNU</h3>
        <p style="color: #a7f3d0; font-size: 12px; margin: 2px 0 0 0;">Professional Binance Futures Quant Terminal</p>
    </div>
""", unsafe_allow_html=True)

# Module Router
if nav_choice == "🏠 Overview / Dashboard":
    df = get_market_overview()

    if not df.empty:
        tab1, tab2, tab3 = st.tabs(["🔥 Top Gainers", "📉 Top Losers", "💎 Top Volume"])

        with tab1:
            st.markdown("#### Top 10 Gainers (24h)")
            gainers = df.sort_values(by='priceChangePercent', ascending=False).head(10)
            for _, row in gainers.iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 8px;">
                        <span style="color: #00F0FF; font-weight: bold;">{row['symbol']}</span>
                        <span style="color: #a7f3d0;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #00FF88; font-weight: bold;">{row['priceChangePercent']:+.2f}%</span>
                    </div>
                """, unsafe_allow_html=True)

        with tab2:
            st.markdown("#### Top 10 Losers (24h)")
            losers = df.sort_values(by='priceChangePercent', ascending=True).head(10)
            for _, row in losers.iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 8px;">
                        <span style="color: #00F0FF; font-weight: bold;">{row['symbol']}</span>
                        <span style="color: #a7f3d0;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #FF4D4D; font-weight: bold;">{row['priceChangePercent']:+.2f}%</span>
                    </div>
                """, unsafe_allow_html=True)

        with tab3:
            st.markdown("#### Top 10 Volume Leaders (24h)")
            volumes = df.sort_values(by='quoteVolume', ascending=False).head(10)
            for _, row in volumes.iterrows():
                st.markdown(f"""
                    <div class="metric-card" style="display: flex; justify-content: space-between; align-items: center; padding: 8px;">
                        <span style="color: #00F0FF; font-weight: bold;">{row['symbol']}</span>
                        <span style="color: #a7f3d0;">${row['lastPrice']:,.4f}</span>
                        <span style="color: #00F0FF;">Vol: ${row['quoteVolume']:,.0f}</span>
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
        else:
            st.warning("Market data not available for advanced filtering.")

    st.markdown("---")
    st.subheader("🤖 Automated Telegram & Whale Scanner (Live)")
    
    status_placeholder = st.empty()
    
    if tg_token and chat_id:
        status_placeholder.info("⚡ Auto-scanner is active in the background. Monitoring volume spikes...")
        
        market_df = get_market_overview()
        if not market_df.empty:
            active_signals = apply_advanced_filters(market_df, tg_token, chat_id)
            if active_signals:
                status_placeholder.success(f"Successfully sent alerts for: {active_signals}")
            else:
                status_placeholder.info("Scan active. Waiting for major volume spikes...")
    else:
        status_placeholder.warning("⚠️ Please enter your Telegram Bot Token and Chat ID in the sidebar to activate auto-alerts.")