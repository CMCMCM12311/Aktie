import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# CSS til layout
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        h1 {margin-top: -1rem; margin-bottom: 0.5rem; font-size: 1.8rem !important; text-align: center;}
        hr {margin-top: 0.5rem; margin-bottom: 0.5rem;}
        .stButton>button {width: 100%; border-radius: 5px; height: 3rem; background-color: #262730; color: white; font-weight: bold;}
        /* Fremhæv afspil-knappen */
        .main-btn>div>button {background-color: #ff4b4b !important; color: white !important;}
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
                "visible": True,
                "x": 0.01, "y": 1.12,
                "buttons": [{
                    "label": "▶ KLIK HER FOR AT AFSPILLE",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 20, "redraw": True}, "fromcurrent": True}]
                }]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Auto-play script (forsøger at klikke på knappen automatisk)
    st.components.v1.html(
        """
        <script>
        function clickPlay() {
            var btn = window.parent.document.querySelector('rect.updatemenu-button-rect');
            if (btn) { btn.dispatchEvent(new MouseEvent('click', {bubbles: true})); }
            else { setTimeout(clickPlay, 300); }
        }
        setTimeout(clickPlay, 500);
        </script>
        """, height=0
    )

# --- KONTROLPANEL (NEDENUNDER) ---
st.write("---")
col_input, col_play = st.columns([3, 1])

with col_input:
    new_t = st.text_input("Tickers", value=st.session_state.tickers_val, label_visibility="collapsed")

with col_play:
    # Den nye knap der erstatter "Compare"
    st.markdown('<div class="main-btn">', unsafe_allow_html=True)
    if st.button("Opdater & Afspil 🚀"):
        st.session_state.tickers_val = new_t
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Tids-knapper
t_cols = st.columns(5)
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
vals = [1, 5, 10, 20, "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()
