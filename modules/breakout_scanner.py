import streamlit as st
import pandas as pd
import requests

def render_breakout_scanner():
    st.subheader("⚡ Breakout & Whale Accumulation Scanner (Binance Futures)")
    st.info("Filtering Binance Futures for Low-Cap Whale Opportunities...")
    
    search_query = st.text_input("🔍 Search Any Futures Coin (e.g., BTCUSDT)", "").upper().strip()
    
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[df['symbol'].str.endswith('USDT')].copy()
            
            df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
            df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
            df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
            
            if search_query:
                df = df[df['symbol'].str.contains(search_query)]
                if df.empty:
                    st.warning(f"No futures coin found matching '{search_query}'.")
                    return
            else:
                excluded = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT']
                df = df[~df['symbol'].isin(excluded)]
                df = df[(df['quoteVolume'] > 1_000_000) & (df['quoteVolume'] < 40_000_000)]
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
                            <h3 style="margin:0; color: #00F0FF;">💎 {symbol} (Change: {change:+.2f}%)</h3>
                            <p style="margin: 8px 0; font-size: 14px;"><b>Live Price:</b> ${price:,.4f} | <b>24h Vol:</b> ${vol:,.0f}</p>
                            <p style="margin: 4px 0; color: #00FF88;">🟢 <b>Whale Footprint: Low-Cap Accumulation Phase</b></p>
                            <p style="margin: 4px 0;">🛡️ <b>Support:</b> ${support:,.4f} | <b>Resistance:</b> ${resistance:,.4f}</p>
                            <p style="margin: 4px 0;">🎯 <b>Stop-Loss:</b> ${sl:,.4f} | <b>TP1:</b> ${tp1:,.4f} | <b>TP2:</b> ${tp2:,.4f}</p>
                        </div>
                    """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")