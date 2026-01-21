import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration til bred visning uden sidebar
st.set_page_config(page_title="Aktie-Animator Pro", layout="wide", initial_sidebar_state="collapsed")

st.title("🎬 Aktie-Animator")

# --- DATA SEKTION ---
# Vi definerer disse først, så de er klar til grafen
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 5

ticker_list = [t.strip().upper() for t in st.session_state.tickers_val.split(",")]
start_date = (datetime.now() - timedelta(days=st.session_state.years_val*365)).strftime('%Y-%m-%d')

@st.cache_data
def get_data(tickers, start):
    try:
        df = yf.download(tickers, start=start)['Close']
        if df.empty: return None
        return (df / df.iloc[0]) * 100
    except:
        return None

data = get_data(ticker_list, start_date)

# --- GRAF SEKTION (ØVERST) ---
if data is not None:
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines") for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], title="Dato"),
            yaxis=dict(title="Vækst (Start = 100)"),
            height=550,
            margin=dict(t=20, b=20),
            template="plotly_dark",
            hovermode="x unified",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "x": 0.01, "y": 1.1, "xanchor": "left", "yanchor": "top",
                "buttons": [
                    {"label": "▶ Afspil", "method": "animate", "args": [None, {"frame": {"duration": 15, "redraw": True}, "fromcurrent": True}]},
                    {"label": "⏸ Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]}
                ]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), 10)]
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Kunne ikke hente data. Tjek venligst dine tickers.")

# --- KONTROLPANEL (NEDENUNDER) ---
st.write("---") # En lille adskillelseslinje
col1, col2 = st.columns([2, 2])

with col1:
    new_tickers = st.text_input("Indtast tickers (f.eks. AAPL, BTC-USD)", value=st.session_state.tickers_val)
    if new_tickers != st.session_state.tickers_val:
        st.session_state.tickers_val = new_tickers
        st.rerun()

with col2:
    st.write("Vælg tidsperiode:")
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    if t_col1.button("1 år"): 
        st.session_state.years_val = 1
        st.rerun()
    if t_col2.button("5 år"): 
        st.session_state.years_val = 5
        st.rerun()
    if t_col3.button("10 år"): 
        st.session_state.years_val = 10
        st.rerun()
    if t_col4.button("Alt"): 
        st.session_state.years_val = 20
        st.rerun()

st.caption(f"Aktuel visning: {st.session_state.tickers_val} over de sidste {st.session_state.years_val} år.")
