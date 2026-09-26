import requests

import pandas as pd

import numpy as np





BINANCE_BASE = "https://fapi.binance.com"



EXCLUDED_SYMBOLS = {

    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",

    "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",

}





# ============================================================

# BASIC DATA

# ============================================================



def fetch_trading_symbols():

    try:

        r = requests.get(

            f"{BINANCE_BASE}/fapi/v1/exchangeInfo",

            timeout=10

        )

        r.raise_for_status()



        data = r.json()



        return [

            x["symbol"]

            for x in data.get("symbols", [])

            if x.get("status") == "TRADING"

            and x.get("quoteAsset") == "USDT"

            and x.get("contractType") == "PERPETUAL"

        ]



    except Exception as e:

        print("Symbol error:", e)

        return []





def fetch_futures_tickers():

    try:

        r = requests.get(

            f"{BINANCE_BASE}/fapi/v1/ticker/24hr",

            timeout=10

        )

        r.raise_for_status()



        df = pd.DataFrame(r.json())



        if df.empty:

            return df



        for col in [

            "lastPrice",

            "volume",

            "quoteVolume",

            "priceChangePercent",

            "highPrice",

            "lowPrice",

        ]:

            df[col] = pd.to_numeric(

                df[col],

                errors="coerce"

            )



        return df



    except Exception as e:

        print("Ticker error:", e)

        return pd.DataFrame()





def fetch_klines(symbol, interval, limit=150):

    try:

        r = requests.get(

            f"{BINANCE_BASE}/fapi/v1/klines",

            params={

                "symbol": symbol,

                "interval": interval,

                "limit": limit,

            },

            timeout=10

        )

        r.raise_for_status()



        data = r.json()



        if not isinstance(data, list) or len(data) < 60:

            return pd.DataFrame()



        columns = [

            "open_time", "open", "high", "low", "close",

            "volume", "close_time", "quote_volume",

            "trades", "taker_buy_base", "taker_buy_quote",

            "ignore"

        ]



        df = pd.DataFrame(

            data,

            columns=columns

        )



        for col in [

            "open", "high", "low", "close",

            "volume", "quote_volume",

            "taker_buy_base", "taker_buy_quote"

        ]:

            df[col] = pd.to_numeric(

                df[col],

                errors="coerce"

            )



        return df



    except Exception:

        return pd.DataFrame()





# ============================================================

# INDICATORS

# ============================================================



def calculate_indicators(df):



    df = df.copy()



    df["ema20"] = (

        df["close"]

        .ewm(span=20, adjust=False)

        .mean()

    )



    df["ema50"] = (

        df["close"]

        .ewm(span=50, adjust=False)

        .mean()

    )



    previous_close = df["close"].shift(1)



    tr1 = df["high"] - df["low"]



    tr2 = (

        df["high"] - previous_close

    ).abs()



    tr3 = (

        df["low"] - previous_close

    ).abs()



    df["tr"] = pd.concat(

        [tr1, tr2, tr3],

        axis=1

    ).max(axis=1)



    df["atr"] = (

        df["tr"]

        .rolling(14)

        .mean()

    )



    df["volume_ma20"] = (

        df["volume"]

        .rolling(20)

        .mean()

    )



    df["volume_ratio"] = (

        df["volume"]

        / df["volume_ma20"]

    )



    df["range"] = (

        df["high"] - df["low"]

    )



    df["body"] = (

        df["close"] - df["open"]

    ).abs()



    df["body_ratio"] = np.where(

        df["range"] > 0,

        df["body"] / df["range"],

        0

    )



    # RSI

    delta = df["close"].diff()



    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)



    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()



    rs = (

        avg_gain

        / avg_loss.replace(0, np.nan)

    )



    df["rsi"] = (

        100 - (100 / (1 + rs))

    )



    return df





# ============================================================

# TREND

# ============================================================



def get_trend(df):



    row = df.iloc[-1]



    close = float(row["close"])

    ema20 = float(row["ema20"])

    ema50 = float(row["ema50"])



    if close > ema20 > ema50:

        return "BULLISH"



    if close < ema20 < ema50:

        return "BEARISH"



    if close > ema20:

        return "BULLISH"



    if close < ema20:

        return "BEARISH"



    return "RANGE"





# ============================================================

# RECENT SUPPORT / RESISTANCE

# ============================================================



def get_levels(df):



    lookback = df.iloc[-31:-2]



    support = float(

        lookback["low"].min()

    )



    resistance = float(

        lookback["high"].max()

    )



    return support, resistance





# ============================================================

# BREAKOUT / BREAKDOWN

# ============================================================



def get_structure(df):



    support, resistance = get_levels(df)



    current = df.iloc[-1]



    close = float(current["close"])

    high = float(current["high"])

    low = float(current["low"])



    if close > resistance:



        return {

            "direction": "LONG",

            "label": "BREAKOUT",

            "level": resistance,

            "score": 22,

        }



    if close < support:



        return {

            "direction": "SHORT",

            "label": "BREAKDOWN",

            "level": support,

            "score": 22,

        }



    # Check higher-low structure

    recent = df.tail(12)



    first_low = float(

        recent.iloc[:6]["low"].min()

    )



    second_low = float(

        recent.iloc[6:]["low"].min()

    )



    if second_low > first_low:



        return {

            "direction": "LONG",

            "label": "HIGHER_LOW",

            "level": second_low,

            "score": 12,

        }



    # Check lower-high structure

    first_high = float(

        recent.iloc[:6]["high"].max()

    )



    second_high = float(

        recent.iloc[6:]["high"].max()

    )



    if second_high < first_high:



        return {

            "direction": "SHORT",

            "label": "LOWER_HIGH",

            "level": second_high,

            "score": 12,

        }



    return {

        "direction": "NEUTRAL",

        "label": "RANGE",

        "level": close,

        "score": 2,

    }





# ============================================================

# LIQUIDITY SWEEP

# ============================================================



def get_liquidity(df):



    previous = df.iloc[-22:-2]

    current = df.iloc[-1]



    previous_high = float(

        previous["high"].max()

    )



    previous_low = float(

        previous["low"].min()

    )



    high = float(current["high"])

    low = float(current["low"])

    close = float(current["close"])



    # Bearish high sweep

    if high > previous_high and close < previous_high:



        return {

            "direction": "SHORT",

            "label": "HIGH_SWEEP",

            "score": 8,

        }



    # Bullish low sweep

    if low < previous_low and close > previous_low:



        return {

            "direction": "LONG",

            "label": "LOW_SWEEP",

            "score": 8,

        }



    return {

        "direction": "NEUTRAL",

        "label": "NONE",

        "score": 0,

    }





# ============================================================

# CANDLE CONFIRMATION

# ============================================================



def get_candle_confirmation(df):



    recent = df.tail(5)



    bullish = int(

        (

            recent["close"]

            > recent["open"]

        ).sum()

    )



    bearish = int(

        (

            recent["close"]

            < recent["open"]

        ).sum()

    )



    last = recent.iloc[-1]



    body_ratio = float(

        last["body_ratio"]

    )



    if bullish >= 4 and body_ratio >= 0.50:



        return "LONG", 10



    if bearish >= 4 and body_ratio >= 0.50:



        return "SHORT", 10



    if bullish > bearish:



        return "LONG", 5



    if bearish > bullish:



        return "SHORT", 5



    return "NEUTRAL", 0





# ============================================================

# VOLUME

# ============================================================



def get_volume(df):



    ratio = float(

        df.iloc[-1]["volume_ratio"]

    )



    if ratio >= 3:

        return 18, "STRONG"



    if ratio >= 2:

        return 14, "EXPANDING"



    if ratio >= 1.5:

        return 10, "EARLY"



    if ratio >= 1:

        return 4, "NORMAL"



    return 0, "WEAK"





# ============================================================

# OI

# ============================================================



def fetch_oi(symbol):



    try:



        r = requests.get(

            f"{BINANCE_BASE}/futures/data/openInterestHist",

            params={

                "symbol": symbol,

                "period": "1h",

                "limit": 5,

            },

            timeout=10

        )



        data = r.json()



        if isinstance(data, list) and len(data) >= 2:



            first = float(

                data[0]["sumOpenInterest"]

            )



            last = float(

                data[-1]["sumOpenInterest"]

            )



            if first > 0:



                return (

                    (last - first)

                    / first

                ) * 100



    except Exception:

        pass



    return 0.0





def fetch_funding(symbol):



    try:



        r = requests.get(

            f"{BINANCE_BASE}/fapi/v1/fundingRate",

            params={

                "symbol": symbol,

                "limit": 3,

            },

            timeout=10

        )



        data = r.json()



        if isinstance(data, list) and data:



            return float(

                data[-1]["fundingRate"]

            )



    except Exception:

        pass



    return 0.0





# ============================================================

# DIRECTION SCORE

# ============================================================



def score_direction(

    direction,

    trend_1h,

    trend_15m,

    structure,

    liquidity,

    candle_direction,

    volume_score,

    oi_change,

    funding,

    rsi

):



    score = 0



    if direction == "LONG":



        if trend_1h == "BULLISH":

            score += 20



        if trend_15m == "BULLISH":

            score += 10



        if structure["direction"] == "LONG":

            score += structure["score"]



        if liquidity["direction"] == "LONG":

            score += liquidity["score"]



        if candle_direction == "LONG":

            score += 10



        score += volume_score



        # OI

        if oi_change >= 2:

            score += 8

        elif oi_change >= 1:

            score += 4

        elif oi_change <= -2:

            score -= 3



        # Funding

        if 0 <= funding <= 0.0001:

            score += 5

        elif funding > 0.0003:

            score -= 5



        # RSI

        if 50 <= rsi <= 68:

            score += 8

        elif 68 < rsi <= 72:

            score += 3

        elif rsi > 75:

            score -= 12



    else:



        if trend_1h == "BEARISH":

            score += 20



        if trend_15m == "BEARISH":

            score += 10



        if structure["direction"] == "SHORT":

            score += structure["score"]



        if liquidity["direction"] == "SHORT":

            score += liquidity["score"]



        if candle_direction == "SHORT":

            score += 10



        score += volume_score



        # OI

        if oi_change >= 2:

            score += 8

        elif oi_change >= 1:

            score += 4

        elif oi_change <= -2:

            score -= 3



        # Funding

        if -0.0001 <= funding <= 0:

            score += 5

        elif funding < -0.0003:

            score -= 5



        # RSI

        if 32 <= rsi <= 50:

            score += 8

        elif 28 <= rsi < 32:

            score += 3

        elif rsi < 25:

            score -= 12



    return max(

        0,

        min(100, int(score))

    )





# ============================================================

# REVERSAL DETECTION

# ============================================================



def detect_long_reversal(df):
    """Confirm SHORT -> LONG only after support reclaim + structure confirmation."""
    if len(df) < 40:
        return False

    support, _ = get_levels(df)
    recent = df.tail(12)
    last = recent.iloc[-1]

    # Support interaction/reclaim must have happened recently.
    touched = float(recent["low"].min()) <= support * 1.008
    reclaimed = float(last["close"]) > support

    # Higher-low: the later swing low must be meaningfully above the earlier swing low.
    first_low = float(recent.iloc[:6]["low"].min())
    second_low = float(recent.iloc[6:-1]["low"].min())
    higher_low = second_low > first_low * 1.001

    # Break a local swing high after the higher-low.
    swing_high = float(recent.iloc[:6]["high"].max())
    structure_break = float(last["close"]) > swing_high

    bullish = float(last["close"]) > float(last["open"])
    volume_ok = float(last["volume_ratio"]) >= 1.10

    return all([touched, reclaimed, higher_low, structure_break, bullish, volume_ok])


def detect_short_reversal(df):
    """Confirm LONG -> SHORT only after resistance rejection + structure confirmation."""
    if len(df) < 40:
        return False

    _, resistance = get_levels(df)
    recent = df.tail(12)
    last = recent.iloc[-1]

    touched = float(recent["high"].max()) >= resistance * 0.992
    rejected = float(last["close"]) < resistance

    first_high = float(recent.iloc[:6]["high"].max())
    second_high = float(recent.iloc[6:-1]["high"].max())
    lower_high = second_high < first_high * 0.999

    swing_low = float(recent.iloc[:6]["low"].min())
    structure_break = float(last["close"]) < swing_low

    bearish = float(last["close"]) < float(last["open"])
    volume_ok = float(last["volume_ratio"]) >= 1.10

    return all([touched, rejected, lower_high, structure_break, bearish, volume_ok])


def build_entry_zone(df, direction, structure):
    """
    Build a normalized, structure-based entry zone.

    Invariants:
      LONG  -> zone is below/around current price, low < high
      SHORT -> zone is above/around current price, low < high
    """
    current = float(df.iloc[-1]["close"])
    atr = float(df.iloc[-1]["atr"])

    if not np.isfinite(atr) or atr <= 0:
        atr = max(current * 0.01, 1e-12)

    support, resistance = get_levels(df)
    min_width = max(atr * 0.25, current * 0.001)

    if direction == "LONG":
        base = resistance if structure["label"] == "BREAKOUT" else support

        # Prefer a pullback into support/retest rather than chasing price.
        low = base - atr * 0.35
        high = base + atr * 0.15

        # The zone must not sit materially above current price.
        high = min(high, current - atr * 0.03)

        # If the structural level is already above/too close to current,
        # fall back to a controlled pullback zone below current.
        if high <= low or high <= 0:
            high = current - atr * 0.03
            low = high - min_width

        if high - low < min_width:
            high = max(high, current - atr * 0.03)
            low = high - min_width

        # Keep the wait zone within a reasonable distance.
        low = max(low, current - atr * 1.50)
        high = min(high, current - atr * 0.03)

        if high <= low:
            high = current - atr * 0.03
            low = high - min_width

    else:
        base = support if structure["label"] == "BREAKDOWN" else resistance

        # Prefer a relief rally/retest into resistance rather than chasing short.
        low = base - atr * 0.15
        high = base + atr * 0.35

        # The zone must not sit materially below current price.
        low = max(low, current + atr * 0.03)

        if high <= low or low <= 0:
            low = current + atr * 0.03
            high = low + min_width

        if high - low < min_width:
            low = min(low, current + atr * 0.03)
            high = low + min_width

        high = min(high, current + atr * 1.50)
        low = max(low, current + atr * 0.03)

        if high <= low:
            low = current + atr * 0.03
            high = low + min_width

    low, high = sorted((float(low), float(high)))

    if low <= 0:
        return None

    reference = (low + high) / 2.0

    return {
        "low": low,
        "high": high,
        "reference": reference,
    }


def build_trade_levels(df, direction, zone):
    """Create levels from the zone reference and enforce directional invariants."""
    atr = float(df.iloc[-1]["atr"])
    current = float(df.iloc[-1]["close"])

    if not np.isfinite(atr) or atr <= 0:
        atr = max(current * 0.01, 1e-12)

    support, resistance = get_levels(df)
    entry = float(zone["reference"])

    if direction == "LONG":
        structural_stop = support - atr * 0.15
        volatility_stop = entry - atr * 1.10
        stop = min(structural_stop, volatility_stop)

        # Hard invariant: SL must be below entry.
        if stop >= entry:
            stop = entry - atr * 1.10

        risk = entry - stop
        if risk <= 0:
            return None

        tp1 = entry + risk * 1.50
        tp2 = entry + risk * 2.50

        if not (tp1 > entry > stop and tp2 > tp1):
            return None

    else:
        structural_stop = resistance + atr * 0.15
        volatility_stop = entry + atr * 1.10
        stop = max(structural_stop, volatility_stop)

        # Hard invariant: SL must be above entry.
        if stop <= entry:
            stop = entry + atr * 1.10

        risk = stop - entry
        if risk <= 0:
            return None

        tp1 = entry - risk * 1.50
        tp2 = entry - risk * 2.50

        if not (stop > entry > tp1 and tp1 > tp2):
            return None

    return {
        "entry": entry,
        "stop": float(stop),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "rr": 2.5,
    }


def get_entry_status(current, zone, direction, score, df):
    """Confirmed only when current price is genuinely inside the valid zone."""
    zone_low = float(zone["low"])
    zone_high = float(zone["high"])

    if zone_low > zone_high:
        zone_low, zone_high = zone_high, zone_low

    current = float(current)
    rsi = float(df.iloc[-1]["rsi"])

    inside = zone_low <= current <= zone_high

    if direction == "LONG":
        healthy_rsi = 48 <= rsi <= 70
    else:
        healthy_rsi = 30 <= rsi <= 52

    if inside and score >= 72 and healthy_rsi:
        return "CONFIRMED ENTRY"

    return "WAIT FOR ENTRY"


def analyze_symbol(symbol):



    df_1h = fetch_klines(

        symbol,

        "1h"

    )



    df_15m = fetch_klines(

        symbol,

        "15m"

    )



    if df_1h.empty or df_15m.empty:

        return None



    df_1h = calculate_indicators(

        df_1h

    )



    df_15m = calculate_indicators(

        df_15m

    )



    trend_1h = get_trend(

        df_1h

    )



    trend_15m = get_trend(

        df_15m

    )



    structure = get_structure(

        df_1h

    )



    liquidity = get_liquidity(

        df_1h

    )



    candle_direction, candle_score = (

        get_candle_confirmation(

            df_1h

        )

    )



    volume_score, volume_label = get_volume(

        df_1h

    )



    oi_change = fetch_oi(

        symbol

    )



    funding = fetch_funding(

        symbol

    )



    rsi = float(

        df_1h.iloc[-1]["rsi"]

    )



    current = float(

        df_1h.iloc[-1]["close"]

    )



    # ========================================================

    # LONG SCORE

    # ========================================================



    long_score = score_direction(

        "LONG",

        trend_1h,

        trend_15m,

        structure,

        liquidity,

        candle_direction,

        volume_score,

        oi_change,

        funding,

        rsi

    )



    # ========================================================

    # SHORT SCORE

    # ========================================================



    short_score = score_direction(

        "SHORT",

        trend_1h,

        trend_15m,

        structure,

        liquidity,

        candle_direction,

        volume_score,

        oi_change,

        funding,

        rsi

    )



    # ========================================================

    # ========================================================
    # DIRECTION INVALIDATION
    # ========================================================
    # A broken LONG support invalidates LONG unless a fully confirmed
    # bullish reversal is present. Likewise for SHORT above resistance.
    support, resistance = get_levels(df_1h)
    long_invalidated = current < support and not detect_long_reversal(df_1h)
    short_invalidated = current > resistance and not detect_short_reversal(df_1h)

    if long_invalidated:
        long_score = 0

    if short_invalidated:
        short_score = 0

    # ========================================================
    # REVERSAL BONUS
    # ========================================================

    long_reversal = detect_long_reversal(

        df_1h

    )



    short_reversal = detect_short_reversal(

        df_1h

    )



    if long_reversal:



        long_score += 10



    if short_reversal:



        short_score += 10



    long_score = min(

        100,

        long_score

    )



    short_score = min(

        100,

        short_score

    )



    # ========================================================

    # SELECT DIRECTION

    # ========================================================



    if long_score > short_score:



        direction = "LONG"

        score = long_score



        reversal = long_reversal



    elif short_score > long_score:



        direction = "SHORT"

        score = short_score



        reversal = short_reversal



    else:



        return None



    # Minimum quality

    if score < 62:

        return None



    # Extreme RSI rejection

    if direction == "LONG" and rsi >= 78:

        return None



    if direction == "SHORT" and rsi <= 22:

        return None



    # ========================================================

    # ENTRY ZONE

    # ========================================================



    zone = build_entry_zone(

        df_1h,

        direction,

        structure

    )



    if zone is None:

        return None



    # ========================================================

    # TRADE LEVELS

    # ========================================================



    levels = build_trade_levels(

        df_1h,

        direction,

        zone

    )



    if levels is None:

        return None



    # ========================================================

    # ENTRY STATUS

    # ========================================================



    status = get_entry_status(

        current,

        zone,

        direction,

        score,

        df_1h

    )



    # ========================================================

    # REVERSAL LABEL

    # ========================================================



    if reversal:



        setup_type = "REVERSAL"



    else:



        setup_type = "TREND"



    # ========================================================

    # RESULT

    # ========================================================



    return {

        "symbol": symbol,



        "direction": direction,



        "score": score,



        "confidence": score,



        "status": status,



        "setup_type": setup_type,



        "current": current,



        "wait_low": zone["low"],



        "wait_high": zone["high"],



        "entry": levels["entry"],



        "stop": levels["stop"],



        "tp1": levels["tp1"],



        "tp2": levels["tp2"],



        "rr": levels["rr"],



        # Backend data

        "rsi": rsi,



        "volume_ratio": float(

            df_1h.iloc[-1]["volume_ratio"]

        ),



        "volume_label": volume_label,



        "trend_1h": trend_1h,



        "trend_15m": trend_15m,



        "structure": structure["label"],



        "liquidity": liquidity["label"],



        "oi_change": oi_change,



        "funding": funding,

    }





# ============================================================

# DAILY TOP 5

# ============================================================



def get_daily_candidates(

    max_symbols=50

):



    symbols = fetch_trading_symbols()



    if not symbols:

        return []



    tickers = fetch_futures_tickers()



    if tickers.empty:

        return []



    df = tickers[

        tickers["symbol"].isin(symbols)

    ].copy()



    df = df[

        ~df["symbol"].isin(

            EXCLUDED_SYMBOLS

        )

    ]



    # Avoid extremely illiquid pairs

    df = df[

        (df["quoteVolume"] >= 300_000)

        & (df["quoteVolume"] <= 50_000_000)

    ]



    df = df.sort_values(

        "quoteVolume",

        ascending=False

    )



    df = df.head(

        max_symbols

    )



    print(

        f"Analyzing {len(df)} symbols..."

    )



    results = []



    for symbol in df["symbol"]:



        try:



            result = analyze_symbol(

                symbol

            )



            if result:



                results.append(

                    result

                )



        except Exception as e:



            print(

                f"{symbol}: {e}"

            )



    results.sort(

        key=lambda x: x["confidence"],

        reverse=True

    )



    return results[:5]





# ============================================================

# PRICE FORMAT

# ============================================================



def format_price(value):



    if value >= 100:

        return f"{value:.2f}"



    if value >= 1:

        return f"{value:.4f}"



    if value >= 0.1:

        return f"{value:.5f}"



    if value >= 0.01:

        return f"{value:.6f}"



    return f"{value:.8f}"





# ============================================================

# USER FRIENDLY OUTPUT

# ============================================================



def print_user_output(results):



    print()

    print("======================================")

    print("       VEDHAVISHNU TODAY'S TOP 5")

    print("======================================")

    print()



    if not results:



        print(

            "NO QUALIFIED SETUPS RIGHT NOW."

        )



        return



    for i, item in enumerate(

        results,

        start=1

    ):



        direction_icon = (

            "🟢"

            if item["direction"] == "LONG"

            else "🔴"

        )



        status_icon = (

            "🟢"

            if item["status"] == "CONFIRMED ENTRY"

            else "🟡"

        )



        print(

            f"{i}. {direction_icon} "

            f"{item['symbol']}"

        )



        print(

            f"   {item['direction']}"

        )



        if item["setup_type"] == "REVERSAL":



            print(

                "   🔄 REVERSAL"

            )



        print(

            f"   {status_icon} "

            f"{item['status']}"

        )



        print(

            f"   Current: "

            f"${format_price(item['current'])}"

        )



        if item["status"] == "WAIT FOR ENTRY":



            print(

                f"   Wait: "

                f"${format_price(item['wait_low'])}"

                f" - "

                f"${format_price(item['wait_high'])}"

            )



        else:



            print(

                f"   Entry: "

                f"${format_price(item['entry'])}"

            )



        print(

            f"   🎯 TP1: "

            f"${format_price(item['tp1'])}"

        )



        print(

            f"   🎯 TP2: "

            f"${format_price(item['tp2'])}"

        )



        print(

            f"   🛑 Stop Loss: "

            f"${format_price(item['stop'])}"

        )



        print(

            f"   Confidence: "

            f"{item['confidence']}%"

        )



        print(

            "   -----------------------------"

        )



    print()



    print(

        "Confidence is an internal scanner score, "

        "not a guaranteed win probability."

    )





# ============================================================

# MAIN

# ============================================================



if __name__ == "__main__":



    print()



    print(

        "VEDHAVISHNU DAILY TOP-5 ENGINE V6"

    )



    print(

        "=================================="

    )



    print()



    results = get_daily_candidates(

        max_symbols=50

    )



    print_user_output(

        results

    )
