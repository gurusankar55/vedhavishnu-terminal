import streamlit as st

def render_ui():
    st.markdown("""
        <style>
        /* Global App Background - Premium Deep Midnight Blue / Charcoal */
        .main {
            background-color: #0b0f19;
            color: #f3f4f6 !important;
        }
        .stApp {
            background: linear-gradient(135deg, #0b0f19 0%, #030712 100%);
            color: #f3f4f6 !important;
        }
        
        /* Header Card - Sleek Dark Glassmorphism with Electric Blue Border */
        .header-card {
            background: rgba(17, 24, 39, 0.85);
            border: 1px solid #38bdf8;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(56, 189, 248, 0.15);
            margin-bottom: 24px;
        }
        
        /* Metric & Data Cards */
        .metric-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 12px;
            color: #f3f4f6 !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: #38bdf8;
            box-shadow: 0 4px 20px rgba(56, 189, 248, 0.2);
        }
        
        /* Typography & Headings */
        h1, h2, h3, h4, h5, h6 {
            color: #38bdf8 !important;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        p, span, label, div, b, strong, .stMarkdown, .stText {
            color: #cbd5e1 !important;
        }
        
        /* Custom Buttons */
        .stButton>button {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: #ffffff;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.6rem 1.4rem;
            font-size: 15px;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
            box-shadow: 0 4px 20px rgba(56, 189, 248, 0.5);
            color: #ffffff;
        }
        
        /* Search Textbox Styling */
        .stTextInput>div>div>input {
            background-color: #1e293b !important;
            color: #38bdf8 !important;
            border: 1px solid #334155 !important;
            border-radius: 8px;
            font-weight: 500;
        }
        .stTextInput>div>div>input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #030712;
            border-right: 1px solid #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="header-card">
            <h2 style="margin:0; font-size: 26px; color: #38bdf8;">⚡ VEDHAVISHNU QUANT TERMINAL</h2>
            <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 14px;">Institutional Grade Binance Futures Engine</p>
        </div>
    """, unsafe_allow_html=True)