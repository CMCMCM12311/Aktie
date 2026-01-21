import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration for at undgå scroll og fjerne marginer
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# CSS til stramt layout og skjulning af tekniske knapper
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 0rem;}
        h1 {margin-top: -1rem; margin-bottom: 0.5rem; font-size: 1.8rem !important; text-align: center;}
        hr {margin-top: 0.5rem; margin-bottom: 0.5rem;}
        .stButton>button {width: 100%; border-radius: 5px; height: 3rem;}
        /* Skjul Plotly kontrolbjælken */
        .modebar {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Aktie-Animator")

# --- SESSION STATE ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10
if 'trigger_anim' not in st.session_state:
    st.session_state.trigger_anim = True

# --- KONTROLPANEL (PLACERET ØVERST FOR FLOW) ---
col_input, col_compare = st.columns([3, 1])

with col_input:
    # Vi bruger en midlertidig variabel til tekstfeltet
    input_text = st.text_input("Indtast tickers", value=st.session_state.tickers_val, label_visibility="collapsed")

with col_compare:
    if st.button("✨ Sammenlign (Compare)"):
        st.session_state.tickers_val = input_text
        st.session_state.trigger_anim = True
        st.rerun()

# Tids-knapper som direkte actions
t_cols = st.columns(5)
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
vals = [1, 5, 10, 20, "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.session_state.trigger_anim = True
        st.rerun()

# --- DATA & GRAF ---
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

if data is not None:
    step = max(1, len(data) // 80) # Justeret for balanceret hastighed
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines", line=dict(width=3)) for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False),
            yaxis=dict(title="Vækst (Start = 100)", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            height=400, # Lav højde for at undgå scroll
            margin=dict(t=10, b=10, l=10, r=10),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons", "showactive": False, "visible": False,
                "buttons": [{"label": "Play", "method": "animate", 
                             "args": [None, {"frame": {"duration": 20, "redraw": True}, "fromcurrent": True}]}]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Auto-play script (kører kun hvis trigger_anim er True)
    if st.session_state.trigger_anim:
        st.components.v1.html(
            """
            <script>
            setTimeout(function() {
                var btn = window.parent.document.querySelector('rect.updatemenu-button-rect');
                if(btn) btn.dispatchEvent(new MouseEvent('click', {bubbles:true}));
            }, 300);
            </script>
            """,
            height=0
        )
        st.session_state.trigger_anim = False

else:
    st.warning("Indtast tickers og tryk 'Sammenlign'")
