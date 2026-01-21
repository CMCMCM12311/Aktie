import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# Apple Design System - Opstrammet UI
st.markdown("""
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1100px;}
        h1 { font-family: -apple-system, sans-serif; color: #1d1d1f; font-weight: 600; text-align: center; margin-bottom: 0.5rem;}
        
        /* Knapper og Input */
        .stButton>button {
            border-radius: 10px; background-color: #f5f5f7;
            color: #1d1d1f; border: 1px solid #d2d2d7; font-weight: 500; font-size: 0.85rem;
            transition: all 0.2s;
        }
        .stButton>button:hover { background-color: #e8e8ed; color: #0071e3; border-color: #0071e3; }
        .stTextInput>div>div>input { border-radius: 12px; border: 1px solid #d2d2d7; height: 3rem; font-size: 1rem;}
        
        .section-label { font-size: 0.85rem; color: #86868b; margin: 10px 0 5px 0; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

# Session State
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# Top 20 mest populære
popular_tickers = ["NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT", "GOOGL", "NFLX", "AMD", "MSTR", 
                   "HOOD", "COIN", "PLTR", "BABA", "MARA", "RIOT", "INTC", "PYPL", "DIS", "JPM"]

# --- FEJLSIKRET DATA FUNKTION ---
@st.cache_data(show_spinner=False)
def get_clean_data(tickers_str, years_val):
    try:
        ticker_list = list(set([t.strip().upper() for t in tickers_str.split(",") if t.strip()]))
        if not ticker_list: return None
        
        start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
        
        # Hent data
        raw_data = yf.download(ticker_list, start=start)['Close']
        
        # Håndtering af både enkelte og flere tickers (pandas formatering)
        if isinstance(raw_data, pd.Series):
            df = raw_data.to_frame()
            df.columns = [ticker_list[0]]
        else:
            df = raw_data
            
        df = df.dropna()
        if df.empty: return None
        
        # Normalisering
        return (df / df.iloc[0]) * 100
    except Exception as e:
        return None

data = get_clean_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF ---
if data is not None:
    apple_colors = ['#0071e3', '#ff3b30', '#34c759', '#af52de', '#ff9500', '#5856d6', '#86868b']
    step = max(1, len(data) // 150)
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=2.5, color=apple_colors[i % len(apple_colors)])) 
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False, fixedrange=True),
            yaxis=dict(range=[0, data.max().max() * 1.1], showgrid=True, gridcolor='#f5f5f7', fixedrange=True),
            height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=80, l=40, r=40), hovermode="x unified",
            updatemenus=[{
                "type": "buttons", "x": 0.5, "y": -0.2, "xanchor": "center", "yanchor": "top",
                "buttons": [
                    {"label": "▶ Spil", "method": "animate", "args": [None, {"frame": {"duration": 40, "redraw": False}, "fromcurrent": True}]},
                    {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("Indtast tickers nedenfor for at generere grafen.")

# --- KONTROLPANEL ---
st.markdown("---")
st.markdown("<div class='section-label'>SØG (Udfyld navne eller tickers adskilt af komma)</div>", unsafe_allow_html=True)
search_input = st.text_input("Søg", placeholder="F.eks: AAPL, Robinhood, NVDA...", label_visibility="collapsed")

if search_input and search_input != st.session_state.tickers_val:
    st.session_state.tickers_val = search_input
    st.rerun()

st.markdown("<div class='section-label'>POPULÆRE LIGE NU</div>", unsafe_allow_html=True)
# Laver 2 rækker med 10 knapper hver
row1 = st.columns(10)
row2 = st.columns(10)

for i, ticker in enumerate(popular_tickers):
    col = row1[i] if i < 10 else row2[i-10]
    if col.button(ticker, key=f"pop_{ticker}"):
        current = [t.strip().upper() for t in st.session_state.tickers_val.split(",") if t.strip()]
        if ticker not in current:
            current.append(ticker)
            st.session_state.tickers_val = ", ".join(current)
            st.rerun()

st.markdown("<div class='section-label'>TIDSHORISONT</div>", unsafe_allow_html=True)
t_cols = st.columns(5)
vals, labels = [1, 5, 10, 20, "IPO"], ["1 år", "5 år", "10 år", "20 år", "IPO"]
for i, col in enumerate(t_cols):
    if col.button(labels[i], key=f"time_{labels[i]}"):
        st.session_state.years_val = vals[i]
        st.rerun()
