import json
import hashlib
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

from modules.ui_layout import render_ui
from modules.daily_top5 import (
    get_daily_candidates,
    format_price,
    analyze_symbol,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="VedhaVishnu Daily Top 5",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL UI
# ============================================================

render_ui()


# ============================================================
# ACTIVE SETUP STORAGE
# ============================================================

TRACKER_FILE = Path(__file__).resolve().parent / "active_setups.json"
MAX_ACTIVE_SETUPS = 5


def load_active_setups():
    """Load persisted active setups from local JSON."""
    if not TRACKER_FILE.exists():
        return {}

    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def save_active_setups(setups):
    """Persist active setups to local JSON."""
    try:
        with open(
            TRACKER_FILE,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                setups,
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception:
        pass


# ============================================================
# TELEGRAM CONFIG FROM STREAMLIT SECRETS
# ============================================================

telegram_cfg = st.secrets.get("telegram", {})

saved_token = str(
    telegram_cfg.get("bot_token", "")
)
saved_chat_id = str(
    telegram_cfg.get("chat_id", "")
)
saved_enabled = bool(
    telegram_cfg.get("enabled", False)
)


# ============================================================
# SESSION STATE
# ============================================================

if "tg_token" not in st.session_state:
    st.session_state["tg_token"] = saved_token

if "chat_id" not in st.session_state:
    st.session_state["chat_id"] = saved_chat_id

if "telegram_enabled" not in st.session_state:
    st.session_state["telegram_enabled"] = saved_enabled

if "last_alert_signature" not in st.session_state:
    st.session_state["last_alert_signature"] = ""

if "last_scan_time" not in st.session_state:
    st.session_state["last_scan_time"] = None

if "active_setups" not in st.session_state:
    st.session_state["active_setups"] = load_active_setups()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        font-size:22px;
        font-weight:700;
        color:#38bdf8;
        margin-bottom:18px;
    ">
        ⚡ Navigation
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.radio(
    "Select Module",
    ["📊 Daily Top 5 V6"],
    index=0,
)


# ============================================================
# TELEGRAM
# ============================================================

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div style="
        font-size:18px;
        font-weight:700;
        color:#f3f4f6;
        margin-bottom:10px;
    ">
        📲 Telegram Alerts
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.checkbox(
    "Enable Telegram Alerts",
    key="telegram_enabled",
)

st.sidebar.text_input(
    "Telegram Bot Token",
    type="password",
    placeholder="Bot Token",
    key="tg_token",
)

st.sidebar.text_input(
    "Telegram Chat ID",
    placeholder="Chat ID",
    key="chat_id",
)


# ============================================================
# TELEGRAM SEND
# ============================================================

def send_telegram_message(message):
    token = st.session_state["tg_token"].strip()
    chat = st.session_state["chat_id"].strip()

    if not token or not chat:
        return False

    try:
        url = (
            f"https://api.telegram.org/"
            f"bot{token}/sendMessage"
        )

        payload = {
            "chat_id": chat,
            "text": message,
            "parse_mode": "Markdown",
        }

        response = requests.post(
            url,
            json=payload,
            timeout=10,
        )

        return response.status_code == 200

    except Exception:
        return False


# ============================================================
# TELEGRAM MESSAGE
# ============================================================

def build_telegram_message(results):
    if not results:
        return (
            "⚡ *VEDHAVISHNU DAILY TOP 5*\n\n"
            "No qualified setups right now."
        )

    lines = [
        "⚡ *VEDHAVISHNU DAILY TOP 5*",
        "",
        f"🕒 `{datetime.now().strftime('%Y-%m-%d %H:%M')}`",
        "",
    ]

    for i, item in enumerate(results, start=1):

        direction = (
            "🟢 LONG"
            if item["direction"] == "LONG"
            else "🔴 SHORT"
        )

        status = (
            "🟢 *CONFIRMED ENTRY*"
            if item["status"] == "CONFIRMED ENTRY"
            else "🟡 *WAIT FOR ENTRY*"
        )

        lines.append(
            f"*{i}. {item['symbol']}*"
        )
        lines.append(direction)

        if item.get("setup_type") == "REVERSAL":
            lines.append("🔄 REVERSAL")

        lines.append(status)

        lines.append(
            f"Current: `${format_price(item['current'])}`"
        )

        if item["status"] == "WAIT FOR ENTRY":
            lines.append(
                f"Wait: "
                f"`${format_price(item['wait_low'])}`"
                f" - "
                f"`${format_price(item['wait_high'])}`"
            )
        else:
            lines.append(
                f"Entry: "
                f"`${format_price(item['entry'])}`"
            )

        lines.append(
            f"🎯 TP1: `${format_price(item['tp1'])}`"
        )
        lines.append(
            f"🎯 TP2: `${format_price(item['tp2'])}`"
        )
        lines.append(
            f"🛑 SL: `${format_price(item['stop'])}`"
        )
        lines.append(
            f"Confidence: `{item['confidence']}%`"
        )
        lines.append("")

    lines.append(
        "_Confidence is an internal scanner score, "
        "not a guaranteed win probability._"
    )

    return "\n".join(lines)


# ============================================================
# ALERT SIGNATURE
# ============================================================

def create_alert_signature(results):
    if not results:
        return "NO_SETUP"

    parts = []

    for item in results:
        parts.append(
            "|".join(
                [
                    str(item.get("symbol", "")),
                    str(item.get("direction", "")),
                    str(item.get("status", "")),
                    str(item.get("setup_type", "")),
                    str(round(float(item.get("wait_low", 0)), 10)),
                    str(round(float(item.get("wait_high", 0)), 10)),
                    str(round(float(item.get("entry", 0)), 10)),
                    str(round(float(item.get("tp1", 0)), 10)),
                    str(round(float(item.get("tp2", 0)), 10)),
                    str(round(float(item.get("stop", 0)), 10)),
                ]
            )
        )

    raw = "||".join(parts)

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# ACTIVE SETUP ENGINE
# ============================================================

def update_active_setups(results):
    """
    Keep important setups alive even when they leave the
    current Top 5 ranking.

    Current Top 5 can change every scan.
    Active setups are tracked separately.
    """

    setups = st.session_state.get(
        "active_setups",
        {},
    )

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # --------------------------------------------------------
    # ADD / UPDATE CURRENT TOP 5
    # --------------------------------------------------------

    for item in results:
        symbol = item.get("symbol")

        if not symbol:
            continue

        status = item.get("status")

        if status not in (
            "WAIT FOR ENTRY",
            "CONFIRMED ENTRY",
        ):
            continue

        existing = setups.get(symbol)

        updated = dict(item)

        if existing:
            updated["first_seen"] = existing.get(
                "first_seen",
                now,
            )

            if existing.get("tracker_status"):
                updated["tracker_status"] = existing.get(
                    "tracker_status"
                )
        else:
            updated["first_seen"] = now

        updated["last_seen"] = now

        setups[symbol] = updated

    # --------------------------------------------------------
    # RE-CHECK ACTIVE SETUPS NOT IN CURRENT TOP 5
    # --------------------------------------------------------

    current_symbols = {
        item.get("symbol")
        for item in results
        if item.get("symbol")
    }

    for symbol in list(setups.keys()):

        if symbol in current_symbols:
            continue

        try:
            fresh = analyze_symbol(symbol)

            if not fresh:
                continue

            old = setups[symbol]

            old_direction = old.get("direction")
            new_direction = fresh.get("direction")

            # Same direction: update the setup.
            if new_direction == old_direction:
                fresh["first_seen"] = old.get(
                    "first_seen",
                    now,
                )
                fresh["last_seen"] = now

                if old.get("tracker_status"):
                    fresh["tracker_status"] = old.get(
                        "tracker_status"
                    )

                setups[symbol] = fresh

            # Opposite direction: only accept an explicit
            # reversal from the V6 engine.
            elif fresh.get("setup_type") == "REVERSAL":
                fresh["first_seen"] = old.get(
                    "first_seen",
                    now,
                )
                fresh["last_seen"] = now
                fresh["tracker_status"] = "REVERSAL"

                setups[symbol] = fresh

            # Otherwise keep the existing setup.
            else:
                old["last_seen"] = now
                setups[symbol] = old

        except Exception:
            continue

    # --------------------------------------------------------
    # CHECK TP / SL
    # --------------------------------------------------------

    for symbol in list(setups.keys()):

        item = setups[symbol]

        try:
            current = float(
                item.get("current", 0) or 0
            )
            tp1 = float(
                item.get("tp1", 0) or 0
            )
            tp2 = float(
                item.get("tp2", 0) or 0
            )
            stop = float(
                item.get("stop", 0) or 0
            )
        except Exception:
            continue

        direction = item.get("direction")

        if current <= 0:
            continue

        if direction == "LONG":

            if current <= stop:
                item["tracker_status"] = "INVALIDATED"

            elif current >= tp2:
                item["tracker_status"] = "TP2 HIT"

            elif current >= tp1:
                item["tracker_status"] = "TP1 HIT"

        elif direction == "SHORT":

            if current >= stop:
                item["tracker_status"] = "INVALIDATED"

            elif current <= tp2:
                item["tracker_status"] = "TP2 HIT"

            elif current <= tp1:
                item["tracker_status"] = "TP1 HIT"

    # --------------------------------------------------------
    # KEEP ONLY LATEST 5 ACTIVE SETUPS
    # --------------------------------------------------------

    if len(setups) > MAX_ACTIVE_SETUPS:
        ordered = sorted(
            setups.items(),
            key=lambda x: x[1].get(
                "last_seen",
                "",
            ),
            reverse=True,
        )

        setups = dict(
            ordered[:MAX_ACTIVE_SETUPS]
        )

    st.session_state["active_setups"] = setups
    save_active_setups(setups)

    return setups


# ============================================================
# ACTIVE SETUP DISPLAY
# ============================================================

def display_active_setups(
    active_setups,
    current_symbols,
):
    hidden_active = {
        symbol: item
        for symbol, item in active_setups.items()
        if symbol not in current_symbols
    }

    if not hidden_active:
        return

    st.markdown("## 🔎 ACTIVE SETUPS")

    for symbol, item in hidden_active.items():

        direction = item.get(
            "direction",
            "WAIT",
        )

        status = item.get(
            "status",
            "WAIT FOR ENTRY",
        )

        tracker_status = item.get(
            "tracker_status",
            "",
        )

        with st.container(border=True):

            if direction == "LONG":
                st.markdown(
                    f"### 🟢 {symbol}"
                )
            else:
                st.markdown(
                    f"### 🔴 {symbol}"
                )

            st.markdown(
                f"**{direction}**"
            )

            if status == "CONFIRMED ENTRY":
                st.success(
                    "🟢 CONFIRMED ENTRY"
                )
            else:
                st.warning(
                    "🟡 WAIT FOR ENTRY"
                )

            if tracker_status:
                st.caption(
                    f"Tracker: {tracker_status}"
                )

            current = item.get(
                "current",
                0,
            )

            st.markdown(
                f"**Current:** "
                f"${format_price(current)}"
            )

            if status == "WAIT FOR ENTRY":
                wait_low = item.get(
                    "wait_low",
                    0,
                )
                wait_high = item.get(
                    "wait_high",
                    0,
                )

                st.markdown(
                    f"**Wait:** "
                    f"${format_price(wait_low)}"
                    f" – "
                    f"${format_price(wait_high)}"
                )
            else:
                entry = item.get(
                    "entry",
                    0,
                )

                st.markdown(
                    f"**Entry:** "
                    f"${format_price(entry)}"
                )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(
                    f"🎯 **TP1**  \n"
                    f"${format_price(item.get('tp1', 0))}"
                )

            with c2:
                st.markdown(
                    f"🎯 **TP2**  \n"
                    f"${format_price(item.get('tp2', 0))}"
                )

            with c3:
                st.markdown(
                    f"🛑 **Stop Loss**  \n"
                    f"${format_price(item.get('stop', 0))}"
                )

            st.markdown(
                f"**Confidence:** "
                f"{item.get('confidence', 0)}%"
            )


# ============================================================
# DAILY TOP 5
# ============================================================

@st.fragment(run_every="15m")
def daily_top5_scanner():

    st.markdown(
        "## 📊 VEDHAVISHNU DAILY TOP 5"
    )

    st.caption(
        "V6 BINANCE FUTURES CONFLUENCE SCANNER"
    )

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    with st.spinner(
        "Scanning Binance Futures..."
    ):
        results = get_daily_candidates(
            max_symbols=50
        )

    # --------------------------------------------------------
    # ACTIVE SETUP TRACKER
    # --------------------------------------------------------

    active_setups = update_active_setups(
        results
    )

    st.session_state[
        "last_scan_time"
    ] = datetime.now()

    # --------------------------------------------------------
    # TELEGRAM AUTO ALERT
    # --------------------------------------------------------

    if st.session_state[
        "telegram_enabled"
    ]:

        signature = create_alert_signature(
            results
        )

        previous_signature = (
            st.session_state[
                "last_alert_signature"
            ]
        )

        if signature != previous_signature:

            message = build_telegram_message(
                results
            )

            sent = send_telegram_message(
                message
            )

            if sent:
                st.session_state[
                    "last_alert_signature"
                ] = signature

                st.toast(
                    "📲 New Top 5 alert sent to Telegram",
                    icon="⚡",
                )

    # --------------------------------------------------------
    # NO SETUPS
    # --------------------------------------------------------

    if not results:
        st.info(
            "No qualified setups right now."
        )

        current_symbols = set()

        display_active_setups(
            active_setups,
            current_symbols,
        )

        return

    # --------------------------------------------------------
    # DISPLAY TOP 5
    # --------------------------------------------------------

    current_symbols = {
        item.get("symbol")
        for item in results
        if item.get("symbol")
    }

    for i, item in enumerate(
        results,
        start=1,
    ):

        symbol = item.get(
            "symbol",
            "UNKNOWN",
        )

        direction = item.get(
            "direction",
            "WAIT",
        )

        status = item.get(
            "status",
            "WAIT FOR ENTRY",
        )

        setup_type = item.get(
            "setup_type",
            "",
        )

        current = item.get(
            "current",
            0,
        )

        with st.container(border=True):

            if direction == "LONG":
                st.markdown(
                    f"### {i}. 🟢 {symbol}"
                )
            else:
                st.markdown(
                    f"### {i}. 🔴 {symbol}"
                )

            st.markdown(
                f"**{direction}**"
            )

            if setup_type == "REVERSAL":
                st.info(
                    "🔄 REVERSAL"
                )

            if status == "CONFIRMED ENTRY":
                st.success(
                    "🟢 CONFIRMED ENTRY"
                )
            else:
                st.warning(
                    "🟡 WAIT FOR ENTRY"
                )

            st.markdown(
                f"**Current:** "
                f"${format_price(current)}"
            )

            if status == "WAIT FOR ENTRY":

                st.markdown(
                    f"**Wait:** "
                    f"${format_price(item.get('wait_low', 0))}"
                    f" – "
                    f"${format_price(item.get('wait_high', 0))}"
                )

            else:

                st.markdown(
                    f"**Entry:** "
                    f"${format_price(item.get('entry', 0))}"
                )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.markdown(
                    f"🎯 **TP1**  \n"
                    f"${format_price(item.get('tp1', 0))}"
                )

            with c2:
                st.markdown(
                    f"🎯 **TP2**  \n"
                    f"${format_price(item.get('tp2', 0))}"
                )

            with c3:
                st.markdown(
                    f"🛑 **Stop Loss**  \n"
                    f"${format_price(item.get('stop', 0))}"
                )

            st.markdown(
                f"**Confidence:** "
                f"{item.get('confidence', 0)}%"
            )

    # --------------------------------------------------------
    # ACTIVE SETUPS
    # --------------------------------------------------------

    display_active_setups(
        active_setups,
        current_symbols,
    )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    if st.session_state[
        "last_scan_time"
    ]:

        scan_time = (
            st.session_state[
                "last_scan_time"
            ].strftime("%H:%M:%S")
        )

        st.caption(
            f"Last scan: {scan_time} • "
            "Auto scan: every 15 minutes"
        )

    st.caption(
        "Confidence is an internal scanner score, "
        "not a guaranteed win probability."
    )


# ============================================================
# START
# ============================================================

daily_top5_scanner()
