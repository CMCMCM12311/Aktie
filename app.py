import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# CSS til Layout-kærlighed og ensartede knapper
st.markdown("""
    <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 0rem;}
        h1 {margin-top: -1rem; margin-bottom: 1rem; font-size: 2rem !important; text-align: center;}
        
        /* Gør alle knapper ens og pæne */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3rem;
            background-color: #262730;
            color: white;
            border: 1px solid #464646;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        .stButton>button:hover {
            border-color: #ff4b4b;
            color: #ff4b4b;
            background-color: #31333f;
        }
        
        /* Skjul Plotly modebar */
        .modebar {display: none !important;}
        
        /* Input felt styling */
        .stTextInput>div>div>input {
            background-color: #262730;
            color: white;
            border-radius: 8px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Aktie-Animator")

# --- SESSION STATE ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# --- SMART DATA CACHING (Gør det lynhurtigt) ---
@st.cache_data(show_spinner=False, ttl=3600) # Gemmer data i 1 time
def get_cached_data(tickers_str, years_val):
    ticker_list = [t.strip().upper() for t in tickers_str.split(",")]
    if years_val == "IPO":
        start = "1900-01-01"
    else:
        start = (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
    
    try:
        df = yf.download(ticker_list, start=start)['Close'].dropna()
        if df.empty: return None
        return (df / df.iloc[0]) * 100
    except: return None

data = get_cached_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF SEKTION ---
if data is not None:
    # Vi bruger færre frames (100) for at gøre selve animationen hurtigere
    step = max(1, len(data) // 100)
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines", line=dict(width=3)) for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False),
            yaxis=dict(title="Vækst (Start = 100)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            height=450,
            margin=dict(t=10, b=80, l=10, r=10),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "x": 0.5, "y": -0.12,
                "xanchor": "center", "yanchor": "top",
                "direction": "left",
                "buttons": [
                    {"label": "▶ AFSPIL ANIMATION", "method": "animate", "args": [None, {"frame": {"duration": 15, "redraw": True}, "fromcurrent": True}]},
                    {"label": "⏸ PAUSE", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.error("Kunne ikke hente data. Tjek venligst dine tickers.")

# --- KONTROLPANEL (ENSARTET UI) ---
st.markdown("<br>", unsafe_allow_html=True) # Lidt luft

# Ticker input i fuld bredde
new_t = st.text_input("Indtast tickers (f.eks. NVDA, AAPL)", value=st.session_state.tickers_val, label_visibility="collapsed")
if new_t != st.session_state.tickers_val:
    st.session_state.tickers_val = new_t
    st.rerun()

# Flotte, ensartede knapper
t_cols = st.columns(5)
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
vals = [1, 5, 10, 20, "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()

st.caption(f"Viser nu: {st.session_state.tickers_val} over {st.session_state.years_val if st.session_state.years_val != 'IPO' else 'max'} år.")
