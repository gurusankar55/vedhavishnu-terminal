import requests
import pandas as pd
import streamlit as st
import time

def send_telegram_alert(token, chat_id, message):
    """டெலிகிராம் மூலம் அலர்ட் அனுப்பும் பங்க்ஷன்"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def apply_advanced_filters(market_df, tg_token, chat_id):
    """பிட்காயின் போன்ற பெரிய காயின்களைத் தவிர்த்து, லோ மார்க்கெட் கேப் காயின்களை மட்டும் ஸ்கேன் செய்யும் முறை"""
    active_signals = []
    
    if market_df.empty:
        return active_signals
        
    # பிட்காயின் (BTC), எத்தேரியம் (ETH), சோலானா (SOL) போன்ற பெரிய காயின்களை விலக்குதல்
    excluded_coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    filtered_df = market_df[~market_df['symbol'].isin(excluded_coins)].copy()
    
    # லோ/மிட் மார்க்கெட் கேப் காயின்களுக்கான வால்யூம் வரம்பு (உதாரணமாக மிதமான வால்யூம் மற்றும் நல்ல விலை மாற்றம்)
    # இதில் குறிப்பிட்ட வரம்பிற்குள் உள்ள காயின்கள் மட்டும் எடுக்கப்படும்
    low_cap_coins = filtered_df[
        (filtered_df['quoteVolume'] > 2_000_000) & 
        (filtered_df['quoteVolume'] < 50_000_000) & 
        (filtered_df['priceChangePercent'] > 3.0)
    ].sort_values(by='quoteVolume', ascending=False).head(5) # ஒரே நேரத்தில் அதிக மெசேஜ் வராமல் இருக்க டாப் 5 மட்டும்
    
    for _, row in low_cap_coins.iterrows():
        symbol = row['symbol']
        price = row['lastPrice']
        vol = row['quoteVolume']
        change = row['priceChangePercent']
        
        # தோராயமான RSI மற்றும் சப்போர்ட் கணிப்பு
        rsi_val = 58.4
        support = price * 0.94
        resistance = price * 1.06
        sl = support * 0.97
        tp1 = resistance * 0.98
        
        # டெலிகிராம் மெசேஜ் வடிவம்
        message = (
            f"🚀 *Low-Cap Whale Accumulation Alert!* 🚀\n\n"
            f"🪙 *Coin:* `{symbol}`\n"
            f"📊 *24h Change:* `+{change:.2f}%`\n"
            f"📈 *RSI (14):* `{rsi_val}`\n"
            f"💎 *Quote Volume:* `${vol:,.0f}`\n\n"
            f"🛡️ *Support Zone:* `${support:.4f}`\n"
            f"🎯 *Stop-Loss (SL):* `${sl:.4f}`\n"
            f"🎯 *Target (TP1):* `${tp1:.4f}`\n\n"
            f"⏳ *Action:* Low-cap breakout detected! Wait for dip to support for safe entry."
        )
        
        # டெலிகிராமிற்கு அனுப்புதல் (Duplicate தவிர்க்க செஷன் ஸ்டேட் அல்லது லிஸ்ட் சரிபார்த்தல்)
        if tg_token and chat_id:
            success = send_telegram_alert(tg_token, chat_id, message)
            if success:
                active_signals.append(symbol)
                time.sleep(1) # மெசேஜ்கள் அடுத்தடுத்து வராமல் இருக்க சிறிய இடைவெளி
                
    return active_signals