import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration for et rent look
st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

# Apple Design System CSS
st.markdown("""
    <style>
        /* Apple-agtig lys baggrund */
        .stApp {
            background-color: #fbfbfd;
        }
        
        .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px;}
        
        /* Overskrift i SF Pro stil */
        h1 {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1d1d1f;
            font-weight: 600;
            letter-spacing: -0.02em;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        /* Minimalistiske knapper */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            height: 2.8rem;
            background-color: #f5f5f7;
            color: #1d1d1f;
            border: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton>button:hover {
            background-color: #e8e8ed;
            color: #0071e3;
        }
        
        /* Input feltet */
        .stTextInput>div>div>input {
            border-radius: 12px;
            border: 1px solid #d2d2d7;
            padding: 10px;
            text-align: center;
            background-color: white;
        }

        hr {border-top: 1px solid #d2d2d7; margin: 2rem 0;}
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

# --- SESSION STATE ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

# --- DATA (CACHED) ---
@st.cache_data(show_spinner=False)
def get_clean_data(tickers_str, years_val):
    ticker_list = [t.strip().upper() for t in tickers_str.split(",")]
    start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
    try:
        df = yf.download(ticker_list, start=start)['Close'].dropna()
        return (df / df.iloc[0]) * 100 if not df.empty else None
    except: return None

data = get_clean_data(st.session_state.tickers_val, st.session_state.years_val)

# --- GRAF SEKTION ---
if data is not None:
    # Apples software-palette: Blå, sølvgrå, mørkegrå
    apple_colors = ['#0071e3', '#86868b', '#1d1d1f', '#ff3b30']
    step = max(1, len(data) // 100)
    
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, 
                         line=dict(width=2.5, color=apple_colors[i % len(apple_colors)]),
                         fill='tonexty', fillcolor='rgba(0,113,227,0.02)') # Meget diskret fill
              for i, c in enumerate(data.columns)],
        layout=go.Layout(
            xaxis=dict(showgrid=False, color="#86868b", tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor='#f5f5f7', color="#86868b", tickfont=dict(size=10)),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=100, l=40, r=40),
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "x": 0.5, "y": -0.25, "xanchor": "center", "yanchor": "top",
                "buttons": [
                    {"label": "Spil", "method": "animate", "args": [None, {"frame": {"duration": 20, "redraw": True}, "fromcurrent": True}]},
                    {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.warning("Indtast tickers for at begynde")

# --- KONTROLPANEL ---
new_t = st.text_input("Tickers", value=st.session_state.tickers_val, label_visibility="collapsed")
if new_t != st.session_state.tickers_val:
    st.session_state.tickers_val = new_t
    st.rerun()

t_cols = st.columns(5)
vals = [1, 5, 10, 20, "IPO"]
labels = ["1 år", "5 år", "10 år", "20 år", "IPO"]

for i, col in enumerate(t_cols):
    if col.button(labels[i]):
        st.session_state.years_val = vals[i]
        st.rerun()
