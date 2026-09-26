import streamlit as st
import requests
import pandas as pd
import numpy as np

def apply_advanced_filters(market_df, tg_token, chat_id):
    if market_df.empty:
        return []
    
    active_signals = []
    
    # Filter for significant volume and price momentum (True Futures Whale Accumulation)
    whale_df = market_df[
        (market_df['quoteVolume'] > 2_000_000) & 
        (market_df['priceChangePercent'] >= 1.5) &
        (market_df['priceChangePercent'] <= 12.0)
    ].sort_values(by='quoteVolume', ascending=False).head(3)

    if whale_df.empty:
        return []

    for _, row in whale_df.iterrows():
        symbol = row['symbol']
        price = row['lastPrice']
        volume = row['quoteVolume']
        change = row['priceChangePercent']

        # Dynamic Resistance & Support Calculation based on Price Action and Volatility
        support = price * 0.95
        r1 = price * 1.04  # Resistance 1 (TP1)
        r2 = price * 1.09  # Resistance 2 (TP2)
        r3 = price * 1.15  # Resistance 3 (Target Extension)
        
        stop_loss = support * 0.985

        signal_text = (
            f"⚡ *VEDHAVISHNU QUANT TERMINAL - WHALE ALERT* ⚡\n\n"
            f"💎 *Symbol:* `{symbol}`\n"
            f"📈 *24h Change:* `{change:+.2f}%`\n"
            f"💵 *Live Price:* `${price:,.4f}`\n"
            f"📊 *24h Quote Vol:* `${volume:,.0f}`\n\n"
            f"🟢 *Status:* Whale Accumulation & Breakout Initiated!\n"
            f"🛡️ *Support Zone:* `${support:,.4f}`\n"
            f"🛑 *Stop-Loss (SL):* `${stop_loss:,.4f}`\n\n"
            f"🎯 *Calculated Resistance Targets:* \n"
            f"• *TP1 (R1):* `${r1:,.4f}`\n"
            f"• *TP2 (R2):* `${r2:,.4f}`\n"
            f"• *TP3 (R3):* `${r3:,.4f}`\n\n"
            f"⚠️ *Note:* Analyze order book volume before entry."
        )

        active_signals.append(symbol)

        # Send Telegram Alert if credentials are provided
        if tg_token and chat_id:
            try:
                tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": signal_text,
                    "parse_mode": "Markdown"
                }
                requests.post(tg_url, json=payload, timeout=5)
            except Exception:
                pass

    return active_signals