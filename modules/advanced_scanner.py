import streamlit as st
import requests
import pandas as pd
import numpy as np

def apply_advanced_filters(market_df, tg_token, chat_id):
    if market_df.empty:
        return []
    
    active_signals = []
    
    # Sort strictly by volume and get live active futures data
    sorted_df = market_df.sort_values(by='quoteVolume', ascending=False).head(10)

    if sorted_df.empty:
        return []

    for _, row in sorted_df.iterrows():
        symbol = row['symbol']
        price = row['lastPrice']
        volume = row['quoteVolume']
        change = row['priceChangePercent']

        # Dynamic calculation based strictly on live price change direction
        if change > 1.5:
            phase = "🚀 SMART MONEY ACCUMULATION & PUMP (Long Setup)"
            support = price * 0.95
            resistance = price * 1.06
            stop_loss = support * 0.985
            tp1 = resistance * 0.98
            tp2 = resistance * 1.04
            action_desc = "Price rising with volume. Look for pullback to support for Long entry."
        elif change < -1.5:
            phase = "⚠️ DISTRIBUTION / DUMP PHASE (Short Setup / Correction)"
            resistance = price * 1.05
            support = price * 0.93
            stop_loss = resistance * 1.02
            tp1 = support * 1.02
            tp2 = support * 0.94
            action_desc = "Price dropping under selling pressure. Watch resistance for Short opportunities."
        else:
            phase = "🟢 SIDEWAYS CONSOLIDATION (Waiting for Breakout)"
            support = price * 0.96
            resistance = price * 1.04
            stop_loss = support * 0.98
            tp1 = resistance * 0.99
            tp2 = resistance * 1.03
            action_desc = "Market consolidating in range. Wait for clear breakout direction."

        signal_text = (
            f"⚡ *VEDHAVISHNU QUANT TERMINAL - LIVE SMART MONEY ALERT* ⚡\n\n"
            f"💎 *Symbol:* `{symbol}`\n"
            f"📈 *24h Change:* `{change:+.2f}%`\n"
            f"💵 *Live Price:* `${price:,.4f}`\n"
            f"📊 *24h Volume:* `${volume:,.0f}`\n\n"
            f"⚡ *Phase:* {phase}\n"
            f"🛡️ *Support:* `${support:,.4f}` | 🎯 *Resistance:* `${resistance:,.4f}`\n"
            f"🛑 *Stop-Loss:* `${stop_loss:,.4f}`\n"
            f"📈 *Targets:* TP1: `${tp1:,.4f}` | TP2: `${tp2:,.4f}`\n\n"
            f"💡 *Action:* {action_desc}"
        )

        active_signals.append(symbol)

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