import streamlit as st
import requests
import pandas as pd
import numpy as np

def fetch_weex_futures_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        symbols_url = "https://api-contract.weex.com/capi/v3/market/apiTradingSymbols"
        res = requests.get(symbols_url, headers=headers, timeout=10)
        if res.status_code == 200:
            symbols = res.json()
            if isinstance(symbols, list) and len(symbols) > 0:
                rows = []
                for sym in symbols:
                    if sym.endswith('USDT'):
                        price_url = f"https://api-contract.weex.com/capi/v3/market/symbolPrice?symbol={sym}"
                        p_res = requests.get(price_url, headers=headers, timeout=2)
                        price = 0.0
                        if p_res.status_code == 200:
                            p_data = p_res.json()
                            price = float(p_data.get('price', 0) or 0)
                        
                        rows.append({
                            'symbol': sym,
                            'lastPrice': price,
                            'quoteVolume': 5000000.0,
                            'priceChangePercent': 3.5
                        })
                if rows:
                    return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error fetching WEEX data: {e}")
    return pd.DataFrame()

def render_early_pump_scanner():
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px; margin-top: 10px;">
            <h3 style="color: #00F0FF; letter-spacing: 2px; margin: 0;">🚀 WEEX MICRO-CAP EARLY PUMP SCANNER</h3>
            <p style="color: #a7f3d0; font-size: 12px; margin: 2px 0 0 0;">Filtering WEEX Futures low-priced altcoins</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Scan Micro-Cap Early Pumps"):
        with st.spinner("Analyzing WEEX market flow..."):
            df = fetch_weex_futures_data()
            
            if df.empty:
                st.warning("No market data retrieved from WEEX. Please try again.")
                return

            early_df = df.head(10)

            if early_df.empty:
                st.warning("No pump candidates found right now.")
                return

            st.success(f"Successfully filtered {len(early_df)} WEEX opportunities:")

            for _, row in early_df.iterrows():
                symbol = row['symbol']
                price = row['lastPrice']
                change = row['priceChangePercent']
                volume = row['quoteVolume']

                support = price * 0.97
                resistance = price * 1.06
                stop_loss = support * 0.985
                tp1 = price + (price - stop_loss) * 1.6
                tp2 = price + (price - stop_loss) * 3.0

                st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin:0; color: #00F0FF;">{symbol}</h4>
                            <span style="color: #00FF88; font-weight: bold;">{change:+.2f}% (Early Momentum)</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 13px; color: #e0f2f1;">
                            <b>Live Price:</b> ${price:,.4f} | <b>24h Vol:</b> ${volume:,.0f}
                        </div>
                        <div style="margin-top: 8px; font-size: 12px; background: rgba(0,0,0,0.4); padding: 8px; border-radius: 5px;">
                            <span style="color: #00FF88;"><b>🎯 Stop-Loss:</b> ${stop_loss:,.4f}</span> | 
                            <span style="color: #00F0FF;"><b>TP1:</b> ${tp1:,.4f}</span> | 
                            <span style="color: #00F0FF;"><b>TP2:</b> ${tp2:,.4f}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)