import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1100px;}
        h1 { font-family: -apple-system, sans-serif; color: #1d1d1f; font-weight: 600; text-align: center; margin-bottom: 0.5rem;}
        .stButton>button {
            border-radius: 10px; background-color: #f5f5f7;
            color: #1d1d1f; border: 1px solid #d2d2d7; font-weight: 500; font-size: 0.85rem;
        }
        .stButton>button:hover { background-color: #e8e8ed; color: #0071e3; border-color: #0071e3; }
        .stTextInput>div>div>input { border-radius: 12px; border: 1px solid #d2d2d7; height: 3rem; font-size: 1rem;}
        .section-label { font-size: 0.85rem; color: #86868b; margin: 15px 0 5px 0; font-weight: 600; text-transform: uppercase;}
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

# Session State
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

popular_tickers = ["NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT", "GOOGL", "NFLX", "AMD", "MSTR", 
                   "HOOD", "COIN", "PLTR", "BABA", "MARA", "RIOT", "INTC", "PYPL", "DIS", "JPM"]

# --- OPTIMERET DATA FUNKTION ---
@st.cache_data(show_spinner=False, ttl=3600, max_entries=20)
def get_fast_data(tickers_str, years_val):
    try:
        t_list = list(set([t.strip().upper() for t in tickers_str.replace(',', ' ').split() if t.strip()]))
        if not t_list: return None
        
        start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
        
        # Hent kun 'Close' og brug threads for hurtigere download
        df = yf.download(t_list, start=start, progress=False, threads=True)['Close']
        
        if isinstance(df, pd.Series):
            df = df.to_frame()
            df.columns = [t_list[0]]
            
        return df.dropna() if not df.empty else None
    except:
        return None

# Spinner lagt ind i en container for at undgå layout-spring
placeholder = st.empty()
with st.spinner('Synkroniserer med markedet...'):
    data = get_fast_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF ---
if data is not None:
    apple_colors = ['#0071e3', '#ff3b30', '#34c759', '#af52de', '#ff9500', '#5856d6', '#86868b']
    # Dynamisk step-størrelse for at holde animationen jævn uanset datamængde
    step = max(1, len(data) // 150)
    y_limit = data.max().max() * 1.1

    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=2.5, color=apple_colors[i % len(apple_colors)])) 
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False, fixedrange=True),
            yaxis=dict(range=[0, y_limit], title="Pris i USD", showgrid=True, gridcolor='#f5f5f7', fixedrange=True),
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

# --- KONTROLPANEL ---
st.write("---")
st.markdown("<div class='section-label'>1. Tidshorisont</div>", unsafe_allow_html=True)
t_cols = st.columns(5)
vals, labels = [1, 5, 10, 20, "IPO"], ["1 år", "5 år", "10 år", "20 år", "IPO"]
for i, col in enumerate(t_cols):
    if col.button(labels[i], key=f"t_{labels[i]}"):
        st.session_state.years_val = vals[i]
        st.rerun()

st.markdown("<div class='section-label'>2. Søg eller tilføj tickers</div>", unsafe_allow_html=True)
search_input = st.text_input("Søg", value=st.session_state.tickers_val, label_visibility="collapsed")
if search_input != st.session_state.tickers_val:
    st.session_state.tickers_val = search_input
    st.rerun()

st.markdown("<div class='section-label'>Hurtig tilføj</div>", unsafe_allow_html=True)
row1 = st.columns(10)
row2 = st.columns(10)
for i, ticker in enumerate(popular_tickers):
    col = row1[i] if i < 10 else row2[i-10]
    if col.button(ticker, key=f"p_{ticker}"):
        curr = [t.strip().upper() for t in st.session_state
