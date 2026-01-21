import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration for at minimere marginer og undgå scroll
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# CSS til at stramme layoutet helt op
st.markdown("""
    <style>
        .block-container {padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem;}
        h1 {margin-top: -0.5rem; margin-bottom: 0rem; font-size: 1.5rem !important; text-align: center;}
        .stButton>button {width: 100%;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Aktie-Animator")

# --- SESSION STATE ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# --- DATA HENTNING ---
ticker_list = [t.strip().upper() for t in st.session_state.tickers_val.split(",")]
if st.session_state.years_val == "IPO":
    start_date = "1900-01-01" 
else:
    start_date = (datetime.now() - timedelta(days=st.session_state.years_val*365)).strftime('%Y-%m-%d')

@st.cache_data(show_spinner=False)
def get_data(tickers, start):
    try:
        df = yf.download(tickers, start=start)['Close']
        if df.empty: return None
        return (df / df.iloc[0]) * 100
    except: return None

data = get_data(ticker_list, start_date)

# --- GRAF SEKTION ---
if data is not None:
    # Vi bruger 'steps' for at gøre animationen hurtig og flydende
    step = max(1, len(data) // 100) 
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         mode="lines", line=dict(width=3)) for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False),
            yaxis=dict(title="Vækst (Start = 100)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            height=480, # Optimeret til 1080p uden scroll
            margin=dict(t=30, b=10, l=10, r=10),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "x": 0.05, "y": 1.1, "xanchor": "left", "yanchor": "top",
                "buttons": [{
                    "label": "▶ AFSPIL UDVIKLING",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 10, "redraw": True}, "fromcurrent": True}]
                }]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    # Vis grafen
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    st.info("💡 Tryk på den blå knap 'AFSPIL UDVIKLING' ovenfor for at starte animationen.")
else:
    st.error("Kunne ikke hente data. Tjek venligst dine tickers.")

# --- KONTROLPANEL (LIGE NEDENUNDER) ---
st.markdown("---")
c1, c2 = st.columns([1.5, 3])

with c1:
    new_t = st.text_input("Tickers (f.eks. NVDA, BTC-USD)", value=st.session_state.tickers_val)
    if new_t != st.session_state.tickers_val:
        st.session_state.tickers_val = new_t
        st.rerun()

with c2:
    st.write("Vælg tidshorisont:")
    btns = st.columns(5)
    labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
    vals = [1, 5, 10, 20, "IPO"]
    
    for i, b in enumerate(btns):
        if b.button(labels[i]):
            st.session_state.years_val = vals[i]
            st.rerun()
