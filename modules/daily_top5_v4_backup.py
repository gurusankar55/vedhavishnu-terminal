import requests
import pandas as pd
import numpy as np


BINANCE_BASE = "https://fapi.binance.com"

EXCLUDED_SYMBOLS = {
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
    "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
}


# ============================================================
# BINANCE DATA
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


def fetch_klines(symbol, interval, limit=120):
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

        if not isinstance(data, list) or len(data) < 50:
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
# OI + FUNDING
# ============================================================

def fetch_oi_and_funding(symbol):

    result = {
        "oi_change_pct": 0.0,
        "oi_value": 0.0,
        "funding_rate": 0.0,
    }

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
                result["oi_change_pct"] = round(
                    ((last - first) / first) * 100,
                    2
                )

            result["oi_value"] = float(
                data[-1].get(
                    "sumOpenInterestValue",
                    0
                )
            )

    except Exception:
        pass

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
            result["funding_rate"] = float(
                data[-1]["fundingRate"]
            )

    except Exception:
        pass

    return result


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
# STRUCTURE
# ============================================================

def get_structure(df):

    if len(df) < 30:
        return {
            "direction": "NEUTRAL",
            "label": "NONE",
            "score": 0,
        }

    current = df.iloc[-1]

    previous = df.iloc[-21:-3]

    close = float(current["close"])

    recent_high = float(
        previous["high"].max()
    )

    recent_low = float(
        previous["low"].min()
    )

    if close > recent_high:
        return {
            "direction": "LONG",
            "label": "BREAKOUT",
            "score": 22,
        }

    if close < recent_low:
        return {
            "direction": "SHORT",
            "label": "BREAKDOWN",
            "score": 22,
        }

    # Higher-low check
    recent_lows = df.tail(12)["low"]

    if recent_lows.iloc[-1] > recent_lows.iloc[:6].min():
        return {
            "direction": "LONG",
            "label": "HIGHER_LOW",
            "score": 12,
        }

    # Lower-high check
    recent_highs = df.tail(12)["high"]

    if recent_highs.iloc[-1] < recent_highs.iloc[:6].max():
        return {
            "direction": "SHORT",
            "label": "LOWER_HIGH",
            "score": 12,
        }

    return {
        "direction": "NEUTRAL",
        "label": "RANGE",
        "score": 2,
    }


# ============================================================
# LIQUIDITY SWEEP
# ============================================================

def get_liquidity(df):

    previous = df.iloc[-21:-1]

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

    # High sweep -> bearish rejection
    if high > previous_high and close < previous_high:
        return {
            "direction": "SHORT",
            "score": 8,
            "label": "HIGH_SWEEP",
        }

    # Low sweep -> bullish recovery
    if low < previous_low and close > previous_low:
        return {
            "direction": "LONG",
            "score": 8,
            "label": "LOW_SWEEP",
        }

    return {
        "direction": "NEUTRAL",
        "score": 0,
        "label": "NONE",
    }


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
# CANDLE FLOW
# ============================================================

def get_candle_flow(df):

    recent = df.tail(5)

    bullish = (
        recent["close"]
        > recent["open"]
    ).sum()

    bearish = (
        recent["close"]
        < recent["open"]
    ).sum()

    if bullish >= 4:
        return "LONG", 10

    if bearish >= 4:
        return "SHORT", 10

    if bullish > bearish:
        return "LONG", 5

    if bearish > bullish:
        return "SHORT", 5

    return "NEUTRAL", 0


# ============================================================
# OI SCORE
# ============================================================

def get_oi_score(
    oi_change,
    direction
):

    score = 0

    if direction == "LONG":

        # Price strength + OI building is useful
        if oi_change >= 2:
            score += 8

        elif oi_change >= 1:
            score += 4

        # OI falling means possible short covering,
        # not strong new-long confirmation.
        elif oi_change <= -2:
            score -= 3

    elif direction == "SHORT":

        if oi_change >= 2:
            score += 8

        elif oi_change >= 1:
            score += 4

        elif oi_change <= -2:
            score -= 3

    return score


# ============================================================
# FUNDING SCORE
# ============================================================

def get_funding_score(
    funding,
    direction
):

    # Keep funding as context,
    # not a standalone signal.

    if direction == "LONG":

        if 0 <= funding <= 0.0001:
            return 5

        if funding > 0.0003:
            return -5

    if direction == "SHORT":

        if -0.0001 <= funding <= 0:
            return 5

        if funding < -0.0003:
            return -5

    return 0


# ============================================================
# DIRECTION SCORE
# ============================================================

def calculate_direction_score(
    direction,
    trend_1h,
    trend_15m,
    structure,
    liquidity,
    candle_direction,
    volume_score,
    oi_score,
    funding_score,
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
        score += oi_score
        score += funding_score

        # Healthy long momentum
        if 50 <= rsi <= 68:
            score += 8

        elif 68 < rsi <= 72:
            score += 3

        elif rsi > 75:
            score -= 12

    elif direction == "SHORT":

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
        score += oi_score
        score += funding_score

        # Healthy short momentum
        if 32 <= rsi <= 50:
            score += 8

        elif 28 <= rsi < 32:
            score += 3

        elif rsi < 25:
            score -= 12

    return max(0, min(100, int(score)))


# ============================================================
# ENTRY ZONE
# ============================================================

def calculate_entry_zone(
    df,
    direction,
    structure
):

    current = float(
        df.iloc[-1]["close"]
    )

    atr = float(
        df.iloc[-1]["atr"]
    )

    if not np.isfinite(atr) or atr <= 0:
        atr = current * 0.01

    recent = df.tail(20)

    recent_high = float(
        recent["high"].max()
    )

    recent_low = float(
        recent["low"].min()
    )

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    if direction == "LONG":

        # If breakout is already confirmed,
        # use a small retest area below current price.
        if structure["label"] == "BREAKOUT":

            zone_high = current
            zone_low = max(
                recent_high * 0.995,
                current - atr * 0.60
            )

            # If price is already far above breakout,
            # wait deeper for a pullback.
            extension = (
                current - recent_high
            ) / atr if atr > 0 else 0

            if extension > 0.8:
                zone_high = current - atr * 0.20
                zone_low = current - atr * 0.80

        else:

            zone_high = current
            zone_low = max(
                recent_low,
                current - atr * 0.60
            )

        zone_low = min(
            zone_low,
            zone_high
        )

        return {
            "zone_low": zone_low,
            "zone_high": zone_high,
            "reference": (
                zone_low + zone_high
            ) / 2,
        }

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    if direction == "SHORT":

        if structure["label"] == "BREAKDOWN":

            zone_low = current
            zone_high = min(
                recent_low * 1.005,
                current + atr * 0.60
            )

            extension = (
                recent_low - current
            ) / atr if atr > 0 else 0

            if extension > 0.8:
                zone_low = current + atr * 0.20
                zone_high = current + atr * 0.80

        else:

            zone_low = current
            zone_high = min(
                recent_high,
                current + atr * 0.60
            )

        zone_high = max(
            zone_high,
            zone_low
        )

        return {
            "zone_low": zone_low,
            "zone_high": zone_high,
            "reference": (
                zone_low + zone_high
            ) / 2,
        }

    return None


# ============================================================
# SL + TP BASED ON WAIT ENTRY
# ============================================================

def calculate_trade_levels(
    df,
    direction,
    entry_zone
):

    atr = float(
        df.iloc[-1]["atr"]
    )

    if not np.isfinite(atr) or atr <= 0:
        atr = float(
            df.iloc[-1]["close"]
        ) * 0.01

    recent = df.tail(20)

    recent_low = float(
        recent["low"].min()
    )

    recent_high = float(
        recent["high"].max()
    )

    entry = float(
        entry_zone["reference"]
    )

    # --------------------------------------------------------
    # LONG
    # --------------------------------------------------------

    if direction == "LONG":

        structure_sl = (
            recent_low - atr * 0.10
        )

        atr_sl = (
            entry - atr * 1.20
        )

        stop = min(
            structure_sl,
            atr_sl
        )

        risk = entry - stop

        if risk <= 0:
            return None

        tp1 = entry + risk * 1.5
        tp2 = entry + risk * 2.5

    # --------------------------------------------------------
    # SHORT
    # --------------------------------------------------------

    elif direction == "SHORT":

        structure_sl = (
            recent_high + atr * 0.10
        )

        atr_sl = (
            entry + atr * 1.20
        )

        stop = max(
            structure_sl,
            atr_sl
        )

        risk = stop - entry

        if risk <= 0:
            return None

        tp1 = entry - risk * 1.5
        tp2 = entry - risk * 2.5

    else:
        return None

    rr = 2.5

    return {
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr": rr,
    }


# ============================================================
# CONFIRMED / WAIT
# ============================================================

def determine_entry_status(
    df,
    direction,
    entry_zone,
    structure,
    score
):

    current = float(
        df.iloc[-1]["close"]
    )

    zone_low = float(
        entry_zone["zone_low"]
    )

    zone_high = float(
        entry_zone["zone_high"]
    )

    rsi = float(
        df.iloc[-1]["rsi"]
    )

    # Strong conditions + current price
    # inside/very close to entry zone
    if direction == "LONG":

        inside = (
            zone_low <= current <= zone_high
        )

        healthy_rsi = (
            48 <= rsi <= 70
        )

        if (
            inside
            and score >= 72
            and healthy_rsi
        ):
            return "CONFIRMED ENTRY"

        return "WAIT FOR ENTRY"

    if direction == "SHORT":

        inside = (
            zone_low <= current <= zone_high
        )

        healthy_rsi = (
            30 <= rsi <= 52
        )

        if (
            inside
            and score >= 72
            and healthy_rsi
        ):
            return "CONFIRMED ENTRY"

        return "WAIT FOR ENTRY"

    return "WAIT FOR ENTRY"


# ============================================================
# SINGLE SYMBOL
# ============================================================

def analyze_symbol(symbol):

    df_1h = fetch_klines(
        symbol,
        "1h",
        120
    )

    df_15m = fetch_klines(
        symbol,
        "15m",
        120
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

    volume_score, volume_label = get_volume(
        df_1h
    )

    candle_direction, candle_score = (
        get_candle_flow(df_1h)
    )

    oi_data = fetch_oi_and_funding(
        symbol
    )

    rsi = float(
        df_1h.iloc[-1]["rsi"]
    )

    # --------------------------------------------------------
    # LONG SCORE
    # --------------------------------------------------------

    long_oi_score = get_oi_score(
        oi_data["oi_change_pct"],
        "LONG"
    )

    long_funding_score = get_funding_score(
        oi_data["funding_rate"],
        "LONG"
    )

    long_score = calculate_direction_score(
        "LONG",
        trend_1h,
        trend_15m,
        structure,
        liquidity,
        candle_direction,
        volume_score,
        long_oi_score,
        long_funding_score,
        rsi
    )

    # --------------------------------------------------------
    # SHORT SCORE
    # --------------------------------------------------------

    short_oi_score = get_oi_score(
        oi_data["oi_change_pct"],
        "SHORT"
    )

    short_funding_score = get_funding_score(
        oi_data["funding_rate"],
        "SHORT"
    )

    short_score = calculate_direction_score(
        "SHORT",
        trend_1h,
        trend_15m,
        structure,
        liquidity,
        candle_direction,
        volume_score,
        short_oi_score,
        short_funding_score,
        rsi
    )

    # --------------------------------------------------------
    # Select direction
    # --------------------------------------------------------

    if long_score >= short_score:
        direction = "LONG"
        score = long_score
    else:
        direction = "SHORT"
        score = short_score

    # Don't force weak setups
    if score < 62:
        return None

    # --------------------------------------------------------
    # Extreme RSI rejection
    # --------------------------------------------------------

    if direction == "LONG" and rsi >= 78:
        return None

    if direction == "SHORT" and rsi <= 22:
        return None

    # --------------------------------------------------------
    # Entry zone
    # --------------------------------------------------------

    entry_zone = calculate_entry_zone(
        df_1h,
        direction,
        structure
    )

    if entry_zone is None:
        return None

    levels = calculate_trade_levels(
        df_1h,
        direction,
        entry_zone
    )

    if levels is None:
        return None

    status = determine_entry_status(
        df_1h,
        direction,
        entry_zone,
        structure,
        score
    )

    current = float(
        df_1h.iloc[-1]["close"]
    )

    return {
        "symbol": symbol,
        "direction": direction,
        "score": score,

        "status": status,

        "current_price": current,

        "wait_low": entry_zone["zone_low"],
        "wait_high": entry_zone["zone_high"],

        # IMPORTANT:
        # TP/SL are calculated from the
        # entry-zone reference, NOT blindly
        # from current price.
        "entry": levels["entry"],
        "stop": levels["stop"],
        "tp1": levels["tp1"],
        "tp2": levels["tp2"],

        "rr": levels["rr"],

        "confidence": score,

        # Backend diagnostics
        "rsi": round(rsi, 2),
        "volume_ratio": round(
            float(
                df_1h.iloc[-1]["volume_ratio"]
            ),
            2
        ),
        "volume_label": volume_label,
        "trend_1h": trend_1h,
        "trend_15m": trend_15m,
        "structure": structure["label"],
        "liquidity": liquidity["label"],
        "oi_change_pct": oi_data[
            "oi_change_pct"
        ],
        "funding_rate": oi_data[
            "funding_rate"
        ],
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

    # Liquidity universe
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

    results = []

    print(
        f"Analyzing {len(df)} symbols..."
    )

    for symbol in df["symbol"]:

        try:

            result = analyze_symbol(
                symbol
            )

            if result:
                results.append(result)

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
# SIMPLE USER OUTPUT
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

        print(
            f"   {status_icon} "
            f"{item['status']}"
        )

        print(
            f"   Current: "
            f"${format_price(item['current_price'])}"
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
        "Note: Confidence is an internal "
        "scanner score, not a guaranteed "
        "win probability."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "VEDHAVISHNU DAILY TOP-5 ENGINE V4"
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