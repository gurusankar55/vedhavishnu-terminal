import streamlit as st

def render_ui():
    # Custom CSS for Professional Quant Terminal Theme with Neon Cyan Accents
    st.markdown("""
        <style>
        .main {
            background-color: #0b251f;
            color: #e0f2f1;
        }
        .stApp {
            background: linear-gradient(135deg, #0b251f 0%, #061511 100%);
        }
        .header-card {
            background: rgba(11, 37, 31, 0.85);
            border: 1px solid #00F0FF;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 240, 255, 0.15);
            margin-bottom: 20px;
        }
        .metric-card {
            background: rgba(16, 53, 44, 0.7);
            border: 1px solid rgba(0, 240, 255, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        h1, h2, h3 {
            color: #00F0FF !important;
            font-family: 'Inter', sans-serif;
        }
        .stButton>button {
            background-color: #00F0FF;
            color: #061511;
            font-weight: bold;
            border-radius: 6px;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #00c2d1;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("""
        <div class="header-card">
            <h2 style="margin:0; font-size: 24px;">⚡ PRO QUANT TERMINAL</h2>
            <p style="color: #a7f3d0; margin: 5px 0 0 0; font-size: 14px;">Modular Institutional Engine for Binance Futures</p>
        </div>
    """, unsafe_allow_html=True)