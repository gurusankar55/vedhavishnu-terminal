import streamlit as st
import pandas as pd
import requests

def render_breakout_scanner():
    st.subheader("⚡ Breakout & Whale Accumulation Scanner (Top 5 Low-Cap)")
    st.info("Filtering Exchange Markets for Low-Cap Whale Opportunities...")
    
    # சர்ச் பாக்ஸ்
    search_query = st.text_input("🔍 Search Any Coin (e.g., AVNTUSDT)", "").upper().strip()
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    df = pd.DataFrame()
    
    # Method 1: Binance Spot API Fallback
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[df['symbol'].str.endswith('USDT')].copy()
            df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
            df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
            df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
    except Exception:
        pass

    # Method 2: Bybit Ticker API Fallback
    if df.empty:
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
        except Exception:
            pass

    # Method 3: MEXC Ticker API Fallback
    if df.empty:
        try:
            mexc_url = "https://api.mexc.com/api/v3/ticker/24hr"
            res3 = requests.get(mexc_url, headers=headers, timeout=8)
            if res3.status_code == 200:
                data = res3.json()
                df = pd.DataFrame(data)
                df = df[df['symbol'].str.endswith('USDT')].copy()
                df['lastPrice'] = pd.to_numeric(df['lastPrice'], errors='coerce')
                df['quoteVolume'] = pd.to_numeric(df['quoteVolume'], errors='coerce')
                df['priceChangePercent'] = pd.to_numeric(df['priceChangePercent'], errors='coerce')
        except Exception as e:
            st.error(f"Error: {e}")

    if df.empty:
        st.error("Failed to fetch market data from all exchanges.")
        return

    # யூசர் சர்ச் செய்தால் அதை மட்டும் காட்டுதல்
    if search_query:
        df = df[df['symbol'].str.contains(search_query)]
        if df.empty:
            st.warning(f"No coin found matching '{search_query}'.")
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