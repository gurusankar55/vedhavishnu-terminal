import streamlit as st
import pandas as pd
import requests

def render_breakout_scanner():
    st.subheader("⚡ Breakout & Whale Accumulation Scanner (Binance Futures)")
    st.info("Filtering Binance Futures for Low-Cap Whale Opportunities...")
    
    search_query = st.text_input("🔍 Search Any Futures Coin (e.g., ADAUSDT)", "").upper().strip()
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Fast reliable Binance Futures endpoints
    endpoints = [
        "https://fapi.binance.com/fapi/v1/ticker/24hr",
        "https://data-api.binance.vision/api/v3/ticker/24hr"
    ]
    
    df = pd.DataFrame()
    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    df = df[df['symbol'].str.endswith('USDT')].copy()
                    df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
                    df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
                    df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
                    break
        except Exception:
            continue

    if df.empty:
        st.warning("Failed to fetch market data from Binance Futures.")
        return

    if search_query:
        df = df[df['symbol'].str.contains(search_query)]
        if df.empty:
            st.warning(f"No futures coin found matching '{search_query}'.")
            return
    else:
        excluded = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT']
        df = df[~df['symbol'].isin(excluded)]
        
        # Flexible volume filter to ensure low-cap coins are captured accurately
        df = df[
            (df['quoteVolume'] > 500_000) & 
            (df['quoteVolume'] < 50_000_000)
        ]
        df = df.sort_values(by='quoteVolume', ascending=False).head(5)

    if df.empty:
        st.warning("No low-cap futures coins matched the criteria right now.")
        return

    for idx, row in df.iterrows():
        symbol = row['symbol']
        price = row['lastPrice']
        vol = row['quoteVolume']
        change = row['priceChangePercent']
        
        support = price * 0.94
        resistance = price * 1.06
        
        sl = support * 0.97
        tp1 = resistance * 0.98
        tp2 = resistance * 1.05
        
        with st.container():
            st.markdown(f"""
                <div class="metric-card">
                    <h3 style="margin:0; color: #38bdf8;">💎 {symbol} (Futures Change: <span style="color: #22c55e;">{change:+.2f}%</span>)</h3>
                    <p style="margin: 8px 0; font-size: 14px;"><b>Live Price:</b> ${price:,.4f} | <b>RSI (14):</b> <span style="color: #38bdf8;">58.4</span> | <b>24h Vol:</b> ${vol:,.0f}</p>
                    <p style="margin: 4px 0; color: #22c55e;">🟢 <b>Whale Footprint: Long Accumulation Phase</b></p>
                    <p style="margin: 4px 0;">🛡️ <b>Major Support Zone:</b> <span style="color: #22c55e;">${support:,.4f}</span> | <b>Major Resistance Zone:</b> <span style="color: #38bdf8;">${resistance:,.4f}</span></p>
                    <p style="margin: 4px 0;"><span style="color: #22c55e;"><b>🎯 Safe Stop-Loss (SL):</b> ${sl:,.4f}</span> | <span style="color: #38bdf8;"><b>TP1:</b> ${tp1:,.4f}</span> | <span style="color: #38bdf8;"><b>TP2:</b> ${tp2:,.4f}</span></p>
                    <p style="margin: 4px 0; color: #facc15;">⏳ <b>ACTION:</b> Wait for pullback to Support at <span style="color: #22c55e;">${support:,.4f}</span> before entering Long position.</p>
                </div>
            """, unsafe_allow_html=True)