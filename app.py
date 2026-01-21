import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Aktie-Animator", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #fbfbfd; }
        .block-container {padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1000px;}
        h1 { font-family: -apple-system, sans-serif; color: #1d1d1f; font-weight: 600; text-align: center; }
        .stButton>button {
            border-radius: 12px; height: 3rem; background-color: #f5f5f7;
            color: #1d1d1f; border: none; font-weight: 500;
        }
        .stButton>button:hover { background-color: #e8e8ed; color: #0071e3; }
        .stTextInput>div>div>input { border-radius: 12px; border: 1px solid #d2d2d7; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.title("Aktie-Animator")

if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10

@st.cache_data(show_spinner=False)
def get_clean_data(tickers_str, years_val):
    ticker_list = [t.strip().upper() for t in tickers_str.split(",")]
    start = "1900-01-01" if years_val == "IPO" else (datetime.now() - timedelta(days=int(years_val)*365)).strftime('%Y-%m-%d')
    try:
        df = yf.download(ticker_list, start=start)['Close'].dropna()
        return (df / df.iloc[0]) * 100 if not df.empty else None
    except: return None

data = get_clean_data(st.session_state.tickers_val, st.session_state.years_val)

if data is not None:
    apple_colors = ['#0071e3', '#86868b', '#1d1d1f', '#ff3b30']
    
    # BEDRE FLOW: Vi tager flere skridt (200 punkter i stedet for 100)
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
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=100, l=40, r=40),
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "x": 0.5, "y": -0.25, "xanchor": "center", "yanchor": "top",
                "buttons": [
                    {
                        "label": "▶ Spil", 
                        "method": "animate", 
                        # LANGSOMMERE: Duration sat til 50ms (0.05 sek pr frame)
                        "args": [None, {"frame": {"duration": 50, "redraw": False}, "fromcurrent": True}]
                    },
                    {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), step)]
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
else:
    st.warning("Indtast tickers")

# KONTROLPANEL
new_t = st.text_input("Tickers", value=st.session_state.tickers_val, label_visibility="collapsed")
if new_t != st.session_state.tickers_val:
    st.session_state.tickers_val
