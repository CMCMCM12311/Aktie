import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# CSS til layout og knapper
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        h1 {margin-top: -1rem; margin-bottom: 0.5rem; font-size: 1.8rem !important; text-align: center;}
        hr {margin-top: 0.5rem; margin-bottom: 0.5rem;}
        /* Styling af den store afspilningsknap */
        .stButton>button {width: 100%; border-radius: 5px; height: 3.5rem; font-weight: bold; font-size: 1.1rem;}
        .play-btn>div>button {background-color: #0083B8 !important; color: white !important; border: none;}
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
        df = yf.download(tickers, start=start)['Close'].dropna()
        if df.empty: return None
        return (df / df.iloc[0]) * 100
    except: return None

data = get_data(ticker_list, start_date)

# --- GRAF SEKTION ---
if data is not None:
    step = max(1, len(data) // 100)
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines", line=dict(width=3)) for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False),
            yaxis=dict(title="Vækst (Start = 100)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            height=450,
            margin=dict(t=10, b=10, l=10, r=10),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "visible": False, # Vi skjuler den tekniske knap i grafen
                "buttons": [{
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 20, "redraw": True}, "fromcurrent": True}]
                }]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.error("Kunne ikke hente data. Tjek tickers.")

# --- KONTROLPANEL (NEDENUNDER) ---
st.write("---")

# Række 1: Tickers og Play
col_input, col_play = st.columns([2, 2])

with col_input:
    new_t = st.text_input("Indtast tickers (tryk Enter for at opdatere)", value=st.session_state.tickers_val)
    if new_t != st.session_state.tickers_val:
        st.session_state.tickers_val = new_t
        st.rerun()

with col_play:
    st.markdown('<div class="play-btn">', unsafe_allow_html=True)
    if st.button("▶ KLIK HER FOR AT AFSPILLE"):
        # JavaScript der trykker på den skjulte knap i grafen
        st.components.v1.html(
            """
            <script>
            var btn = window.parent.document.querySelector('rect.updatemenu-button-rect');
            if (btn) { btn.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
            </script>
            """, height=0
        )
    st.markdown('</div>', unsafe_allow_html=True)

# Række 2: Tids-knapper
t_cols = st.columns(5)
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
vals = [1, 5, 10, 20, "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()

st.caption(f"Status: {st.session_state.tickers_val} | Startdato: {start_date}")
