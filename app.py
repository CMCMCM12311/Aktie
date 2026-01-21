import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# Apple Design System
st.markdown("""
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container {padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1000px;}
        h1 { font-family: -apple-system, sans-serif; color: #1d1d1f; font-weight: 600; text-align: center; }
        .stButton>button {
            border-radius: 12px; background-color: #f5f5f7;
            color: #1d1d1f; border: none; font-weight: 500; font-size: 0.8rem;
        }
        .stButton>button:hover { background-color: #e8e8ed; color: #0071e3; }
        .stTextInput>div>div>input { border-radius: 12px; border: 1px solid #d2d2d7; text-align: center; height: 3.5rem;}
        .popular-label { font-size: 0.8rem; color: #86868b; margin-bottom: 5px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

# Session State
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# Top 20 mest populære tickers
popular_tickers = ["NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT", "GOOGL", "NFLX", "AMD", "MSTR", "HOOD", "COIN", "PLTR", "BABA", "MARA", "RIOT", "INTC", "PYPL", "DIS", "JPM"]

# --- DATA FUNKTION ---
@st.cache_data(show_spinner=False)
def get_clean_data(tickers_str, years_val):
    ticker_list = [t.strip().upper() for t in tickers_str.split(",")]
    start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
    try:
        # Tager kun de nødvendige kolonner for at optimere hastighed
        df = yf.download(ticker_list, start=start)['Close'].dropna()
        if df.empty: return None
        return (df / df.iloc[0]) * 100
    except: return None

data = get_clean_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF ---
if data is not None:
    apple_colors = ['#0071e3', '#86868b', '#1d1d1f', '#ff3b30', '#34c759', '#af52de', '#ff9500']
    step = max(1, len(data) // 200)
    x_range = [data.index.min(), data.index.max()]
    y_range = [0, data.max().max() * 1.1]

    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=2.5, color=apple_colors[i % len(apple_colors)])) 
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(range=x_range, showgrid=False, color="#86868b", fixedrange=True),
            yaxis=dict(range=y_range, showgrid=True, gridcolor='#f5f5f7', color="#86868b", fixedrange=True),
            height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=80, l=40, r=40), hovermode="x unified",
            updatemenus=[{
                "type": "buttons", "x": 0.5, "y": -0.2, "xanchor": "center", "yanchor": "top",
                "buttons": [
                    {"label": "▶ Spil", "method": "animate", "args": [None, {"frame": {"duration": 50, "redraw": False}, "fromcurrent": True}]},
                    {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for i in data.columns]) 
                for i in range(1, len(data), step)]
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- KONTROLPANEL ---
st.markdown("<div class='popular-label'>Søg på navn (f.eks. 'Apple') eller ticker (f.eks. 'AAPL')</div>", unsafe_allow_html=True)
search_input = st.text_input("Søg", placeholder="Indtast navne eller tickers adskilt af komma...", label_visibility="collapsed")

if search_input:
    # Hvis brugeren skriver noget, opdaterer vi listen
    st.session_state.tickers_val = search_input
    st.rerun()

# Vis "Most Popular" knapper
st.markdown("<div class='popular-label'>Populære lige nu:</div>", unsafe_allow_html=True)
pop_cols = st.columns(10) # 2 rækker af 10
for i, ticker in enumerate(popular_tickers):
    if pop_cols[i % 10].button(ticker, key=ticker):
        if ticker not in st.session_state.tickers_val:
            st.session_state.tickers_val += f", {ticker}"
            st.rerun()

st.markdown("---")
t_cols = st.columns(5)
vals, labels = [1, 5, 10, 20, "IPO"], ["1 år", "5 år", "10 år", "20 år", "IPO"]
for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()
