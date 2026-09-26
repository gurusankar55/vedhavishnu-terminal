import streamlit as st


def render_ui():

    st.markdown(
        """
<style>

.stApp {
    background:
        radial-gradient(circle at 15% 10%, rgba(14,165,233,0.08), transparent 30%),
        radial-gradient(circle at 85% 80%, rgba(59,130,246,0.05), transparent 35%),
        linear-gradient(135deg, #020617 0%, #0b1120 50%, #020617 100%);
    color: #f8fafc !important;
}

.main {
    background: transparent !important;
}

/* ================= SIDEBAR ================= */

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, #020617 0%, #07111f 55%, #020617 100%);
    border-right: 1px solid rgba(56,189,248,0.14);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}

[data-testid="stSidebar"] h2 {
    color: #f8fafc !important;
    font-size: 17px !important;
    font-weight: 800 !important;
    letter-spacing: 0.8px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] {
    margin-top: 5px;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    min-height: 44px !important;
    padding: 0 13px !important;
    margin: 5px 0 !important;
    border: 1px solid transparent !important;
    border-radius: 11px !important;
    background: rgba(15,23,42,0.45) !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(30,41,59,0.9) !important;
    border-color: rgba(56,189,248,0.22) !important;
    transform: translateX(2px);
}

[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background:
        linear-gradient(
            90deg,
            rgba(14,165,233,0.20),
            rgba(14,165,233,0.06)
        ) !important;

    border-color: rgba(56,189,248,0.42) !important;

    box-shadow:
        inset 3px 0 0 #38bdf8,
        0 5px 18px rgba(14,165,233,0.08) !important;
}

[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #f8fafc !important;
    font-weight: 800 !important;
}

/* ================= SIDEBAR INPUTS ================= */

[data-testid="stSidebar"] input {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 9px !important;
}

[data-testid="stSidebar"] input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 1px rgba(56,189,248,0.15) !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(148,163,184,0.10) !important;
    margin: 18px 0 !important;
}

/* ================= HEADER ================= */

.vv-header {
    background:
        linear-gradient(135deg, #0f172a, #082f49);

    border: 1px solid rgba(56,189,248,0.30);

    border-radius: 16px;

    padding: 20px 24px;

    margin-bottom: 20px;

    box-shadow:
        0 12px 35px rgba(0,0,0,0.30);
}

.vv-header-title {
    color: #f8fafc;
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 1.5px;
}

.vv-header-subtitle {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 5px;
    letter-spacing: 1px;
}

/* ================= BUTTONS ================= */

.stButton > button {
    background:
        linear-gradient(135deg, #0284c7, #0369a1) !important;

    color: white !important;

    border: 1px solid rgba(56,189,248,0.30) !important;

    border-radius: 10px !important;

    font-weight: 700 !important;

    box-shadow:
        0 5px 18px rgba(14,165,233,0.18);

    transition: all 0.15s ease !important;
}

.stButton > button:hover {
    transform: translateY(-1px);

    box-shadow:
        0 8px 24px rgba(14,165,233,0.28);
}

/* ================= CARDS ================= */

.metric-card {
    background:
        linear-gradient(
            135deg,
            rgba(15,23,42,0.92),
            rgba(30,41,59,0.70)
        );

    border: 1px solid rgba(56,189,248,0.16);

    padding: 15px;

    border-radius: 12px;

    margin-bottom: 10px;

    color: #f8fafc !important;

    box-shadow:
        0 6px 22px rgba(0,0,0,0.25);
}

.metric-card:hover {
    border-color: rgba(56,189,248,0.38);
    transform: translateY(-1px);
}

/* ================= TEXT ================= */

h1, h2, h3, h4, h5, h6 {
    color: #e0f2fe !important;
    font-family: "Inter", sans-serif;
}

p {
    color: #cbd5e1;
}

/* ================= INPUT ================= */

.stTextInput input {
    background: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 9px !important;
}

.stTextInput input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 10px rgba(56,189,248,0.18) !important;
}

/* ================= SCROLLBAR ================= */

::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}

::-webkit-scrollbar-track {
    background: #020617;
}

::-webkit-scrollbar-thumb {
    background: #1e3a5f;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #0284c7;
}

</style>
""",
        unsafe_allow_html=True
    )

    # VEDHAVISHNU HEADER
    st.markdown(
        """
        <div class="vv-header">
            <div class="vv-header-title">
                ⚡ VEDHAVISHNU
                <span style="color:#64748b;">QUANT TERMINAL</span>
            </div>
            <p style="
                color:#94a3b8;
                font-size:12px;
                margin:5px 0 0 0;
                letter-spacing:1px;
            ">
                BINANCE FUTURES • MARKET INTELLIGENCE • V6 ENGINE
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )