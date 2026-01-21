import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS til mønster-baggrund og styling
st.markdown("""
    <style>
        /* Baggrund med et diskret grid-mønster */
        .stApp {
            background-color: #0e1117;
            background-image: linear-gradient(#1e2127 1px, transparent 1px), 
                              linear-gradient(90deg, #1e2127 1px, transparent 1px);
            background-size: 40px 40px;
        }
        
        .block-container {padding-top: 1.5rem; padding-bottom: 0rem;}
        h1 {color: #ffffff; text-shadow: 0 0 10px rgba(255,255,255,0.2); text-align: center; margin-bottom: 1rem;}
        
        /* Styling af knapper */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3rem;
            background-color: rgba(38, 39, 48, 0.8);
            color: white;
            border: 1px solid #464646;
            backdrop-filter: blur(5px);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            border-color: #00fbff; /* Cyan lys ved hover */
            box-shadow: 0 0 15px rgba(0, 251, 255, 0.3);
            color: #00fbff;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Aktie-Animator")

# --- DATA SEKTION ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

@st.cache_data(show_spinner=False)
def get_cached_data(tickers_str, years_val):
    ticker_list = [t.strip().upper() for t in tickers_str.split(",")]
    start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
    try:
        df = yf.download(ticker_list, start=start)['Close'].dropna()
        return (df / df.iloc[0]) * 100 if not df.empty else None
    except: return None

data = get_cached_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF SEKTION ---
if data is not None:
    # Neon farver til linjerne
    colors = ['#00fbff', '#ff5500', '#ccff00', '#ff00ff', '#ffffff']
    step = max(1, len(data) // 100)
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=4, color=colors[i % len(colors)])) 
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], showgrid=False, color="white"),
            yaxis=dict(title="Vækst (Start = 100)", showgrid=True, gridcolor='rgba(255,255,255,0.05)', color="white"),
            height=450,
            # Gør graf-baggrunden gennemsigtig
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=80, l=10, r=10),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "x": 0.5, "y": -0.15, "xanchor": "center", "yanchor": "top",
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
    st.error("Data kunne ikke hentes.")

# --- KONTROLPANEL ---
new_t = st.text_input("Tickers", value=st.session_state.tickers_val, label_visibility="collapsed")
if new_t != st.session_state.tickers_val:
    st.session_state.tickers_val = new_t
    st.rerun()

t_cols = st.columns(5)
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]
vals = [1, 5, 10, 20, "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()
