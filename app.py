import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# 1. Grundlæggende konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# 2. Apple Design System (Clean UI)
st.markdown("""
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 1100px;}
        h1 { font-family: -apple-system, sans-serif; color: #1d1d1f; font-weight: 600; text-align: center; margin-bottom: 1rem;}
        
        /* Knapper og Input styling */
        .stButton>button {
            border-radius: 10px; background-color: #f5f5f7;
            color: #1d1d1f; border: 1px solid #d2d2d7; font-weight: 500; font-size: 0.85rem;
            height: 2.8rem; transition: all 0.2s;
        }
        .stButton>button:hover { background-color: #e8e8ed; color: #0071e3; border-color: #0071e3; }
        .stTextInput>div>div>input { border-radius: 12px; border: 1px solid #d2d2d7; height: 3.2rem; font-size: 1rem;}
        
        .section-label { font-size: 0.8rem; color: #86868b; margin: 15px 0 5px 0; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;}
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

# 3. Session State (Hukommelse)
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# Liste over populære aktier
popular_tickers = ["NVDA", "TSLA", "AAPL", "AMZN", "META", "MSFT", "GOOGL", "NFLX", "AMD", "MSTR", 
                   "HOOD", "COIN", "PLTR", "BABA", "MARA", "RIOT", "INTC", "PYPL", "DIS", "JPM"]

# 4. Fejlsikret Data Hentning
@st.cache_data(show_spinner=False)
def get_safe_data(tickers_str, years_val):
    try:
        # Rens ticker-listen
        ticker_list = list(set([t.strip().upper() for t in tickers_str.replace(',', ' ').split() if t.strip()]))
        if not ticker_list: return None
        
        # Beregn startdato
        start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
        
        # Hent data (Close priser)
        df = yf.download(ticker_list, start=start, progress=False)['Close']
        
        # Vigtigt: Håndter hvis df er en Series (kun 1 aktie valgt)
        if isinstance(df, pd.Series):
            df = df.to_frame()
            df.columns = [ticker_list[0]]
        
        df = df.dropna()
        return df if not df.empty else None
    except:
        return None

data = get_safe_data(st.session_state.tickers_val, st.session_state.years_val)

# 5. Graf Sektion (Med Dynamisk Y-akse i USD)
if data is not None:
    apple_colors = ['#0071e3', '#ff3b30', '#34c759', '#af52de', '#ff9500', '#5856d6', '#86868b']
    
    # Indstillinger for animation
    step = max(1, len(data) // 150)
    y_max = data.max().max() * 1.1 # Dynamisk top med 10% luft
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=2.5, color=apple_colors[i % len(apple_colors)])) 
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False, fixedrange=True),
            yaxis=dict(range=[0, y_max], title="Pris (USD)", showgrid=True, gridcolor='#f5f5f7', fixedrange=True),
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
    st.info("Brug knapperne eller søgefeltet nedenfor for at starte.")

# 6. Kontrolpanel (Ryffet rundt efter dine ønsker)
st.write("---")

# Tidshorisont Øverst
st.markdown("<div class='section-label'>1. Vælg tidshorisont</div>", unsafe_allow_html=True)
t_cols = st.columns(5)
vals, labels = [1, 5, 10, 20, "IPO"], ["1 år", "5 år", "10 år", "20 år", "IPO"]
for i, col in enumerate(t_cols):
    if col.button(labels[i], key=f"t_{labels[i]}"):
        st.session_state.years_val = vals[i]
        st.rerun()

# Søgefelt
st.markdown("<div class='section-label'>2. Søg (Ticker eller Navn)</div>", unsafe_allow_html=True)
new_input = st.text_input("Søg", value=st.session_state.tickers_val, label_visibility="collapsed")
if new_input != st.session_state.tickers_val:
    st.session_state.tickers_val = new_input
    st.rerun()

# Populære knapper (Opdaterer søgefeltet)
st.markdown("<div class='section-label'>Hurtig tilføj</div>", unsafe_allow_html=True)
p_rows = [st.columns(10), st.columns(10)]
for i, ticker in enumerate(popular_tickers):
    row_idx = 0 if i < 10 else 1
    col_idx = i % 10
    if p_rows[row_idx][col_idx].button(ticker, key=f"btn_{ticker}"):
        current = [t.strip().upper() for t in st.session_state.tickers_val.replace(',', ' ').split() if t.strip()]
        if ticker not in current:
            current.append(ticker)
            st.session_state.tickers_val = ", ".join(current)
            st.rerun()
