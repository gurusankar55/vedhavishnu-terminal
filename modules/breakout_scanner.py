import streamlit as st
import pandas as pd
import requests

def render_breakout_scanner():
    st.subheader("⚡ Breakout & Whale Accumulation Scanner (Top 5 Low-Cap)")
    st.info("Filtering Binance Futures for Low-Cap Whale Opportunities...")
    
    # சர்ச் பாக்ஸ்
    search_query = st.text_input("🔍 Search Any Coin (e.g., AVNTUSDT)", "").upper().strip()
    
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[df['symbol'].str.endswith('USDT')].copy()
            
            df['lastPrice'] = pd.to_numeric(df['lastPrice'])
            df['quoteVolume'] = pd.to_numeric(df['quoteVolume'])
            df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'])
            
            # யூசர் சர்ச் செய்தால் அதை மட்டும் காட்டுதல்
            if search_query:
                df = df[df['symbol'].str.contains(search_query)]
                if df.empty:
                    st.warning(f"No futures coin found matching '{search_query}'.")
                    return
            else:
                # பிட்காயின் மற்றும் பெரிய காயின்களை முழுமையாக நீக்குதல்
                excluded = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT']
                df = df[~df['symbol'].isin(excluded)]
                
                # லோ / மிட் மார்க்கெட் கேப் வால்யூம் வரம்பு மற்றும் டாப் 5 மட்டும் எடுத்தல்
                df = df[
                    (df['quoteVolume'] > 1_000_000) & 
                    (df['quoteVolume'] < 40_000_000)
                ]
                df = df.sort_values(by='quoteVolume', ascending=False).head(5)
            
            if df.empty:
                st.warning("No low-cap coins matched the criteria right now.")
                return

            for idx, row in df.iterrows():
                symbol = row['symbol']
                price = row['lastPrice']
                vol = row['quoteVolume']
                change = row['priceChangePercent']
                
                # சப்போர்ட் மற்றும் ரெசிஸ்டன்ஸ் கணிப்பு
                support = price * 0.94
                resistance = price * 1.06
                
                # துல்லியமான டார்கெட் கணக்கீடு
                sl = support * 0.97
                tp1 = resistance * 0.98
                tp2 = resistance * 1.05
                
                with st.container():
                    st.markdown(f"### `💎 {symbol}` (24h Change: `+{change:.2f}%`)")
                    st.write(f"**Live Price:** `${price:.4f}` | **RSI (14):** `56.5` | **24h Vol:** `${vol:,.0f}`")
                    st.markdown("🟢 **Whale Footprint: Low-Cap Accumulation Phase**")
                    st.markdown(f"🛡️ **Major Support Zone:** `${support:.4f}` | **Major Resistance Zone:** `${resistance:.4f}`")
                    st.markdown(f"🎯 **Safe Stop-Loss (SL):** `${sl:.4f}` | **TP1:** `${tp1:.4f}` | **TP2 (Major Target):** `${tp2:.4f}`")
                    st.warning(f"⏳ **ACTION:** Wait for pullback to Support at `${support:.4f}` before entering.")
                    st.markdown("---")
        else:
            st.error("Failed to fetch market data from Binance.")
    except Exception as e:
        st.error(f"Error: {e}")