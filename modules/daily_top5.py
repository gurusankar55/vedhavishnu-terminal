import requests
import pandas as pd
import numpy as np


BINANCE_BASE = "https://fapi.binance.com"

EXCLUDED_SYMBOLS = {
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
}


# ============================================================
# BINANCE DATA
# ============================================================

def fetch_trading_symbols():
    url = f"{BINANCE_BASE}/fapi/v1/exchangeInfo"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        symbols = []

        for item in data.get("symbols", []):
            if (
                item.get("status") == "TRADING"
                and item.get("quoteAsset") == "USDT"
                and item.get("contractType") == "PERPETUAL"
            ):
                symbols.append(item["symbol"])

        return symbols

    except Exception as e:
        print(f"Symbol fetch error: {e}")
        return []


def fetch_futures_tickers():
    url = f"{BINANCE_BASE}/fapi/v1/ticker/24hr"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        df = pd.DataFrame(response.json())

        if df.empty:
            return df

        numeric_cols = [
            "lastPrice",
            "volume",
            "quoteVolume",
            "priceChangePercent",
            "highPrice",
            "lowPrice",
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        return df

    except Exception as e:
        print(f"Ticker fetch error: {e}")
        return pd.DataFrame()


def fetch_klines(symbol, interval="1h", limit=120):
    url = f"{BINANCE_BASE}/fapi/v1/klines"

    try:
        response = requests.get(
            url,
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list) or len(data) < 50:
            return pd.DataFrame()

        columns = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ]

        df = pd.DataFrame(data, columns=columns)

        numeric_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "taker_buy_base",
            "taker_buy_quote",
        ]

        for col in numeric_cols:
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
        "oi_signal": "OI_FLAT",
    }

    try:

        # -------------------------
        # Open Interest History
        # -------------------------

        oi_url = (
            f"{BINANCE_BASE}/futures/data/openInterestHist"
        )

        oi_response = requests.get(
            oi_url,
            params={
                "symbol": symbol,
                "period": "1h",
                "limit": 5,
            },
            timeout=10,
        )

        oi_data = oi_response.json()

        if (
            isinstance(oi_data, list)
            and len(oi_data) >= 2
        ):

            first_oi = float(
                oi_data[0]["sumOpenInterest"]
            )

            last_oi = float(
                oi_data[-1]["sumOpenInterest"]
            )

            if first_oi > 0:

                oi_change = (
                    (last_oi - first_oi)
                    / first_oi
                ) * 100

                result["oi_change_pct"] = round(
                    oi_change,
                    2
                )

            result["oi_value"] = float(
                oi_data[-1].get(
                    "sumOpenInterestValue",
                    0
                )
            )

        # -------------------------
        # Funding
        # -------------------------

        funding_url = (
            f"{BINANCE_BASE}/fapi/v1/fundingRate"
        )

        funding_response = requests.get(
            funding_url,
            params={
                "symbol": symbol,
                "limit": 3,
            },
            timeout=10,
        )

        funding_data = funding_response.json()

        if (
            isinstance(funding_data, list)
            and funding_data
        ):

            result["funding_rate"] = float(
                funding_data[-1]["fundingRate"]
            )

        # -------------------------
        # OI Classification
        # -------------------------

        oi_change = result["oi_change_pct"]

        if oi_change >= 2:
            result["oi_signal"] = "OI_BUILDING"

        elif oi_change <= -2:
            result["oi_signal"] = "OI_UNWINDING"

        else:
            result["oi_signal"] = "OI_FLAT"

    except Exception:
        pass

    return result


# ============================================================
# INDICATORS
# ============================================================

def calculate_indicators(df):

    if df.empty:
        return df

    df = df.copy()

    # EMA
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

    # True Range
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

    # ATR
    df["atr"] = (
        df["tr"]
        .rolling(14)
        .mean()
    )

    df["atr_pct"] = (
        df["atr"]
        / df["close"]
    ) * 100

    # Volume
    df["volume_ma20"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    df["volume_ratio"] = (
        df["volume"]
        / df["volume_ma20"]
    )

    # Candle
    df["range"] = (
        df["high"] - df["low"]
    )

    df["body"] = (
        df["close"] - df["open"]
    ).abs()

    df["body_ratio"] = np.where(
        df["range"] > 0,
        df["body"] / df["range"],
        0,
    )

    df["upper_wick"] = (
        df["high"]
        - df[["open", "close"]].max(axis=1)
    )

    df["lower_wick"] = (
        df[["open", "close"]].min(axis=1)
        - df["low"]
    )

    # RSI
    delta = df["close"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = (
        gain
        .rolling(14)
        .mean()
    )

    avg_loss = (
        loss
        .rolling(14)
        .mean()
    )

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    df["rsi"] = (
        100
        - (100 / (1 + rs))
    )

    return df


# ============================================================
# TREND
# ============================================================

def analyze_trend(df):

    if df.empty:
        return {
            "direction": "RANGE",
            "score": 0,
        }

    row = df.iloc[-1]

    close = row["close"]
    ema20 = row["ema20"]
    ema50 = row["ema50"]

    if (
        close > ema20
        and ema20 > ema50
    ):

        return {
            "direction": "BULLISH",
            "score": 20,
        }

    if (
        close < ema20
        and ema20 < ema50
    ):

        return {
            "direction": "BEARISH",
            "score": 20,
        }

    if close > ema20:
        return {
            "direction": "BULLISH",
            "score": 10,
        }

    if close < ema20:
        return {
            "direction": "BEARISH",
            "score": 10,
        }

    return {
        "direction": "RANGE",
        "score": 3,
    }


# ============================================================
# VOLUME FLOW
# ============================================================

def analyze_volume_flow(df):

    if df.empty:
        return {
            "score": 0,
            "label": "WEAK",
        }

    ratio = float(
        df.iloc[-1]["volume_ratio"]
    )

    if ratio >= 3:
        return {
            "score": 20,
            "label": "STRONG_EXPANSION",
        }

    if ratio >= 2:
        return {
            "score": 16,
            "label": "EXPANSION",
        }

    if ratio >= 1.5:
        return {
            "score": 12,
            "label": "EARLY_EXPANSION",
        }

    if ratio >= 1:
        return {
            "score": 6,
            "label": "NORMAL",
        }

    return {
        "score": 0,
        "label": "WEAK",
    }


# ============================================================
# CANDLE FLOW
# ============================================================

def analyze_candle_flow(df):

    if len(df) < 5:
        return {
            "score": 0,
            "direction": "NEUTRAL",
        }

    recent = df.tail(5)

    bullish = (
        recent["close"]
        > recent["open"]
    ).sum()

    bearish = (
        recent["close"]
        < recent["open"]
    ).sum()

    score = 0
    direction = "NEUTRAL"

    if bullish >= 4:

        score = 15
        direction = "BULLISH"

    elif bearish >= 4:

        score = 15
        direction = "BEARISH"

    elif bullish > bearish:

        score = 8
        direction = "BULLISH"

    elif bearish > bullish:

        score = 8
        direction = "BEARISH"

    last_body_ratio = float(
        recent.iloc[-1]["body_ratio"]
    )

    if last_body_ratio >= 0.65:
        score += 5

    return {
        "score": min(score, 20),
        "direction": direction,
    }


# ============================================================
# COMPRESSION
# ============================================================

def analyze_compression(df):

    if len(df) < 45:

        return {
            "score": 0,
            "compression": False,
        }

    recent_range = (
        df.tail(20)["high"].max()
        - df.tail(20)["low"].min()
    )

    previous = df.iloc[-40:-20]

    previous_range = (
        previous["high"].max()
        - previous["low"].min()
    )

    if previous_range <= 0:

        return {
            "score": 0,
            "compression": False,
        }

    ratio = (
        recent_range
        / previous_range
    )

    if ratio <= 0.65:

        return {
            "score": 10,
            "compression": True,
        }

    if ratio <= 0.8:

        return {
            "score": 6,
            "compression": True,
        }

    return {
        "score": 0,
        "compression": False,
    }


# ============================================================
# MARKET STRUCTURE
# ============================================================

def analyze_structure(df):

    if len(df) < 30:

        return {
            "score": 0,
            "direction": "NEUTRAL",
            "label": "NO_STRUCTURE",
        }

    current = df.iloc[-1]

    close = float(current["close"])

    previous = df.iloc[-21:-3]

    recent_high = float(
        previous["high"].max()
    )

    recent_low = float(
        previous["low"].min()
    )

    # Breakout
    if close > recent_high:

        return {
            "score": 20,
            "direction": "BULLISH",
            "label": "BULLISH_BREAKOUT",
        }

    # Breakdown
    if close < recent_low:

        return {
            "score": 20,
            "direction": "BEARISH",
            "label": "BEARISH_BREAKDOWN",
        }

    # Higher low
    lows = df.tail(12)["low"]

    if (
        lows.iloc[-1]
        > lows.iloc[:6].min()
    ):

        return {
            "score": 10,
            "direction": "BULLISH",
            "label": "HIGHER_LOW",
        }

    # Lower high
    highs = df.tail(12)["high"]

    if (
        highs.iloc[-1]
        < highs.iloc[:6].max()
    ):

        return {
            "score": 10,
            "direction": "BEARISH",
            "label": "LOWER_HIGH",
        }

    return {
        "score": 4,
        "direction": "NEUTRAL",
        "label": "RANGE",
    }


# ============================================================
# LIQUIDITY / SWEEP
# ============================================================

def analyze_liquidity(df):

    if len(df) < 25:

        return {
            "score": 0,
            "direction": "NEUTRAL",
            "label": "NONE",
        }

    current = df.iloc[-1]

    previous = df.iloc[-21:-1]

    prev_high = float(
        previous["high"].max()
    )

    prev_low = float(
        previous["low"].min()
    )

    high = float(current["high"])
    low = float(current["low"])
    close = float(current["close"])

    # High sweep and rejection
    if high > prev_high and close < prev_high:

        return {
            "score": 12,
            "direction": "BEARISH",
            "label": "HIGH_LIQUIDITY_SWEEP",
        }

    # Low sweep and recovery
    if low < prev_low and close > prev_low:

        return {
            "score": 12,
            "direction": "BULLISH",
            "label": "LOW_LIQUIDITY_SWEEP",
        }

    return {
        "score": 0,
        "direction": "NEUTRAL",
        "label": "NONE",
    }


# ============================================================
# OI / FUNDING SCORE
# ============================================================

def analyze_oi_funding(
    oi_data,
    direction
):

    score = 0

    oi_change = oi_data["oi_change_pct"]

    funding = oi_data["funding_rate"]

    # OI confirmation
    if oi_change >= 2:

        score += 10

    elif oi_change >= 1:

        score += 5

    elif oi_change <= -2:

        score += 5

    # Funding context
    #
    # Avoid giving maximum score when funding
    # becomes extremely crowded.

    if direction == "LONG":

        if 0 <= funding <= 0.0001:

            score += 5

        elif funding > 0.0003:

            score -= 4

    elif direction == "SHORT":

        if -0.0001 <= funding <= 0:

            score += 5

        elif funding < -0.0003:

            score -= 4

    return score


# ============================================================
# ENTRY / STOP / TARGETS
# ============================================================

def build_trade_levels(
    df,
    direction
):

    row = df.iloc[-1]

    price = float(row["close"])

    atr = float(row["atr"])

    if not np.isfinite(atr) or atr <= 0:

        atr = price * 0.01

    recent = df.tail(20)

    recent_high = float(
        recent["high"].max()
    )

    recent_low = float(
        recent["low"].min()
    )

    if direction == "LONG":

        # Entry around current price
        entry = price

        structure_stop = recent_low

        atr_stop = price - (
            atr * 1.2
        )

        invalidation = min(
            structure_stop,
            atr_stop
        )

        risk = entry - invalidation

        if risk <= 0:
            return None

        tp1 = entry + (
            risk * 1.5
        )

        tp2 = entry + (
            risk * 2.5
        )

    elif direction == "SHORT":

        entry = price

        structure_stop = recent_high

        atr_stop = price + (
            atr * 1.2
        )

        invalidation = max(
            structure_stop,
            atr_stop
        )

        risk = invalidation - entry

        if risk <= 0:
            return None

        tp1 = entry - (
            risk * 1.5
        )

        tp2 = entry - (
            risk * 2.5
        )

    else:

        return None

    rr1 = abs(
        tp1 - entry
    ) / risk

    rr2 = abs(
        tp2 - entry
    ) / risk

    return {
        "entry": round(entry, 8),
        "invalidation": round(
            invalidation,
            8
        ),
        "tp1": round(tp1, 8),
        "tp2": round(tp2, 8),
        "rr1": round(rr1, 2),
        "rr2": round(rr2, 2),
    }


# ============================================================
# EXTENSION FILTER
# ============================================================

def check_extension(
    df,
    direction
):

    if df.empty:
        return False, "NO_DATA"

    row = df.iloc[-1]

    rsi = float(row["rsi"])

    if direction == "LONG":

        if rsi >= 75:

            return True, "OVEREXTENDED_LONG"

    if direction == "SHORT":

        if rsi <= 25:

            return True, "OVEREXTENDED_SHORT"

    return False, "HEALTHY"


# ============================================================
# COMPLETE SYMBOL ANALYSIS
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

    if (
        df_1h.empty
        or df_15m.empty
    ):

        return None

    df_1h = calculate_indicators(
        df_1h
    )

    df_15m = calculate_indicators(
        df_15m
    )

    trend_1h = analyze_trend(
        df_1h
    )

    trend_15m = analyze_trend(
        df_15m
    )

    volume_1h = analyze_volume_flow(
        df_1h
    )

    candle_1h = analyze_candle_flow(
        df_1h
    )

    compression = analyze_compression(
        df_1h
    )

    structure = analyze_structure(
        df_1h
    )

    liquidity = analyze_liquidity(
        df_1h
    )

    # --------------------------------------------------------
    # Determine direction
    # --------------------------------------------------------

    long_votes = 0
    short_votes = 0

    if trend_1h["direction"] == "BULLISH":
        long_votes += 2

    if trend_15m["direction"] == "BULLISH":
        long_votes += 1

    if candle_1h["direction"] == "BULLISH":
        long_votes += 1

    if structure["direction"] == "BULLISH":
        long_votes += 2

    if liquidity["direction"] == "BULLISH":
        long_votes += 1

    if trend_1h["direction"] == "BEARISH":
        short_votes += 2

    if trend_15m["direction"] == "BEARISH":
        short_votes += 1

    if candle_1h["direction"] == "BEARISH":
        short_votes += 1

    if structure["direction"] == "BEARISH":
        short_votes += 2

    if liquidity["direction"] == "BEARISH":
        short_votes += 1

    if long_votes > short_votes:
        direction = "LONG"

    elif short_votes > long_votes:
        direction = "SHORT"

    else:
        direction = "WAIT"

    if direction == "WAIT":
        return None

    # --------------------------------------------------------
    # Base score
    # --------------------------------------------------------

    score = 0

    score += trend_1h["score"]

    score += int(
        trend_15m["score"] * 0.5
    )

    score += volume_1h["score"]

    score += candle_1h["score"]

    score += structure["score"]

    score += liquidity["score"]

    score += compression["score"]

    # --------------------------------------------------------
    # OI + Funding
    # --------------------------------------------------------

    oi_data = fetch_oi_and_funding(
        symbol
    )

    score += analyze_oi_funding(
        oi_data,
        direction
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    rsi = float(
        df_1h.iloc[-1]["rsi"]
    )

    if direction == "LONG":

        if 50 <= rsi <= 68:
            score += 8

        elif 68 < rsi < 75:
            score += 3

        elif rsi >= 75:
            score -= 8

    elif direction == "SHORT":

        if 32 <= rsi <= 50:
            score += 8

        elif 25 < rsi < 32:
            score += 3

        elif rsi <= 25:
            score -= 8

    # --------------------------------------------------------
    # Extension
    # --------------------------------------------------------

    extended, extension_label = check_extension(
        df_1h,
        direction
    )

    # Hard reject extreme extension
    if extended:
        return None

    # --------------------------------------------------------
    # Trade levels
    # --------------------------------------------------------

    levels = build_trade_levels(
        df_1h,
        direction
    )

    if levels is None:
        return None

    # --------------------------------------------------------
    # Minimum R:R
    # --------------------------------------------------------

    if levels["rr2"] < 2:
        return None

    # --------------------------------------------------------
    # Final score cap
    # --------------------------------------------------------

    score = max(
        0,
        min(
            100,
            int(score)
        )
    )

    # Minimum quality threshold
    if score < 60:
        return None

    return {
        "symbol": symbol,
        "direction": direction,
        "score": score,

        "price": round(
            float(df_1h.iloc[-1]["close"]),
            8
        ),

        "rsi": round(
            rsi,
            2
        ),

        "volume_ratio": round(
            float(
                df_1h.iloc[-1]["volume_ratio"]
            ),
            2
        ),

        "volume_flow": volume_1h[
            "label"
        ],

        "trend_1h": trend_1h[
            "direction"
        ],

        "trend_15m": trend_15m[
            "direction"
        ],

        "candle_flow": candle_1h[
            "direction"
        ],

        "structure": structure[
            "label"
        ],

        "liquidity": liquidity[
            "label"
        ],

        "compression": compression[
            "compression"
        ],

        "oi_change_pct": oi_data[
            "oi_change_pct"
        ],

        "oi_signal": oi_data[
            "oi_signal"
        ],

        "funding_rate": oi_data[
            "funding_rate"
        ],

        "entry": levels[
            "entry"
        ],

        "invalidation": levels[
            "invalidation"
        ],

        "tp1": levels[
            "tp1"
        ],

        "tp2": levels[
            "tp2"
        ],

        "rr1": levels[
            "rr1"
        ],

        "rr2": levels[
            "rr2"
        ],

        "extension": extension_label,
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

    valid_symbols = set(symbols)

    df = tickers[
        tickers["symbol"].isin(
            valid_symbols
        )
    ].copy()

    # Remove major pairs
    df = df[
        ~df["symbol"].isin(
            EXCLUDED_SYMBOLS
        )
    ]

    # Liquidity filter
    df = df[
        (df["quoteVolume"] >= 300_000)
        & (df["quoteVolume"] <= 50_000_000)
    ]

    # Sort by volume first
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

            if result is not None:

                results.append(
                    result
                )

        except Exception as e:

            print(
                f"{symbol} error: {e}"
            )

    # Highest score first
    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:5]


# ============================================================
# TERMINAL OUTPUT
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "VEDHAVISHNU DAILY TOP-5 ENGINE V3"
    )
    print(
        "=================================="
    )
    print()

    results = get_daily_candidates(
        max_symbols=50
    )

    if not results:

        print(
            "NO QUALIFIED SETUPS RIGHT NOW."
        )

    else:

        print(
            f"Qualified setups: {len(results)}"
        )
        print()

        for i, item in enumerate(
            results,
            start=1
        ):

            print(
                f"{i}. {item['symbol']}"
            )

            print(
                f"   Direction: {item['direction']}"
            )

            print(
                f"   Score: {item['score']}/100"
            )

            print(
                f"   Price: {item['price']}"
            )

            print(
                f"   RSI: {item['rsi']}"
            )

            print(
                f"   Volume: {item['volume_ratio']}x "
                f"({item['volume_flow']})"
            )

            print(
                f"   Structure: {item['structure']}"
            )

            print(
                f"   Liquidity: {item['liquidity']}"
            )

            print(
                f"   OI: {item['oi_change_pct']}% "
                f"({item['oi_signal']})"
            )

            print(
                f"   Funding: "
                f"{item['funding_rate']}"
            )

            print(
                f"   Entry: {item['entry']}"
            )

            print(
                f"   Invalidation: "
                f"{item['invalidation']}"
            )

            print(
                f"   TP1: {item['tp1']}"
            )

            print(
                f"   TP2: {item['tp2']}"
            )

            print(
                f"   R:R: 1:{item['rr2']}"
            )

            print()

        for i, item in enumerate(
            results,
            start=1
        ):
            ...