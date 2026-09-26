import streamlit as st

def render_ui():
    st.markdown("""
        <style>
        .main {
            background-color: #030d09;
            color: #ffffff !important;
        }
        .stApp {
            background: linear-gradient(135deg, #061f17 0%, #010806 100%);
            color: #ffffff !important;
        }
        .header-card {
            background: rgba(8, 30, 24, 0.98);
            border: 2px solid #00F0FF;
            padding: 22px;
            border-radius: 12px;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.25);
            margin-bottom: 20px;
        }
        .metric-card {
            background: rgba(10, 45, 36, 0.95);
            border: 1px solid rgba(0, 240, 255, 0.4);
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 12px;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }
        h1, h2, h3, h4, h5, h6 {
            color: #00F0FF !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }
        p, span, label, div, b, strong, .stMarkdown, .stText {
            color: #e0f2f1 !important;
        }
        .stButton>button {
            background-color: #00F0FF;
            color: #030d09;
            font-weight: bold;
            border-radius: 8px;
            border: none;
            padding: 0.6rem 1.2rem;
            font-size: 15px;
        }
        .stButton>button:hover {
            background-color: #00c2d1;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.6);
        }
        .stTextInput>div>div>input {
            background-color: #061813 !important;
            color: #00F0FF !important;
            border: 1px solid #00F0FF !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="header-card">
            <h2 style="margin:0; font-size: 26px; color: #00F0FF;">⚡ VEDHAVISHNU QUANT TERMINAL</h2>
            <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">Institutional Binance Futures Engine</p>
        </div>
    """, unsafe_allow_html=True)