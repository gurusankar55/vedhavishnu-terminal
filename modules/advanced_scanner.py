import streamlit as st
import requests
import pandas as pd
import numpy as np

def apply_advanced_filters(market_df, tg_token, chat_id):
    if market_df.empty:
        return []
    
    active_signals = []
    
    # Filter true futures for potential Smart Money accumulation & pump/dump phases
    filtered_df = market_df[
        (market_df['quoteVolume'] > 1_000_000) & 
        (market_df['quoteVolume'] <= 50_000_000)
    ].sort_values(by='quoteVolume', ascending=False).head(5)

    if filtered_df.empty:
        return []

    for _, row in filtered_df.iterrows():
        symbol = row['symbol']
        price = row['lastPrice']
        volume = row['quoteVolume']
        change = row['priceChangePercent']

        # Determine phase based on price momentum and volume action
        if change >= 2.0:
            phase = "🚀 PUMP / DISTRIBUTION PHASE (Smart Money might flip to Short)"
            color_code = "#ef4444"
            support = price * 0.94
            resistance = price * 1.05
            stop_loss = resistance * 1.025
            tp1 = support * 1.02
            tp2 = support * 0.95
            action_desc = "Price pumped. Watch for distribution and potential Short setup near Resistance."
        elif change <= -2.0:
            phase = "⚠️ DUMP / RETAIL TRAP PHASE (Possible Liquidity Sweep)"
            color_code = "#facc15"
            support = price * 0.92
            resistance = price * 1.06
            stop_loss = support * 0.97
            tp1 = resistance * 0.98
            tp2 = resistance * 1.04
            action_desc = "Sharp drop. Wait for volume absorption before catching knife or entering Long."
        else:
            phase = "🟢 SMART MONEY ACCUMULATION PHASE (Sideways Absorption)"
            color_code = "#22c55e"
            support = price * 0.96
            resistance = price * 1.06
            stop_loss = support * 0.985
            tp1 = price + (price - stop_loss) * 1.6
            tp2 = price + (price - stop_loss) * 3.0
            action_desc = "Whales accumulating quietly near support. Prepare for Long breakout."

        signal_text = (
            f"⚡ *VEDHAVISHNU QUANT TERMINAL - SMART MONEY ALERT* ⚡\n\n"
            f"💎 *Symbol:* `{symbol}`\n"
            f"📈 *24h Change:* `{change:+.2f}%`\n"
            f"💵 *Live Price:* `${price:,.4f}`\n"
            f"📊 *24h Quote Vol:* `${volume:,.0f}`\n\n"
            f"⚡ *Market Phase:* {phase}\n"
            f"🛡️ *Support Zone:* `${support:,.4f}`\n"
            f"🎯 *Resistance Zone:* `${resistance:,.4f}`\n"
            f"🛑 *Stop-Loss (SL):* `${stop_loss:,.4f}`\n"
            f"📈 *Targets:* TP1: `${tp1:,.4f}` | TP2: `${tp2:,.4f}`\n\n"
            f"💡 *Action:* {action_desc}"
        )

        active_signals.append(symbol)

        # Trigger Telegram alert if credentials are active
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