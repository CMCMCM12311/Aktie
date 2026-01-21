import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration til bred visning uden sidebar
st.set_page_config(page_title="Aktie-Animator Pro", layout="wide", initial_sidebar_state="collapsed")

st.title("🎬 Aktie-Animator")

# Kontrolpanel placeret over grafen
col_a, col_b = st.columns([2, 1])

with col_a:
    tickers_input = st.text_input("Indtast tickers (adskilt af komma)", "MSFT, MSTR")

with col_b:
    st.write("Vælg tidsperiode:")
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    years = 0
    if t_col1.button("1 år"): years = 1
    if t_col2.button("5 år"): years = 5
    if t_col3.button("10 år"): years = 10
    if t_col4.button("Alt"): years = 20 # Går langt tilbage

# Beregn startdato
if years > 0:
    start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
else:
    start_date = "2015-01-01"

ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

@st.cache_data
def get_data(tickers, start):
    try:
        df = yf.download(tickers, start=start)['Close']
        if df.empty: return None
        # Normalisering til indeks 100
        return (df / df.iloc[0]) * 100
    except:
        return None

data = get_data(ticker_list, start_date)

if data is not None:
    # Selve graf-opbygningen
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines") for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], title="Dato"),
            yaxis=dict(title="Vækst (Start = 100)"),
            height=600, # Gør grafen dejlig høj
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "x": 0.01, "y": 1.15, "xanchor": "left", "yanchor": "top",
                "buttons": [{
                    "label": "▶ Afspil Udvikling",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 15, "redraw": True}, "fromcurrent": True}]
                },
                {
                    "label": "⏸ Pause",
                    "method": "animate",
                    "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]
                }]
            }]
        ),
        # Vi tager hver 10. række for at holde det lynhurtigt
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), 10)]
    )

    fig.update_layout(template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"Viser data fra {start_date} til i dag. Alle kurser er normaliseret til 100 på startdatoen for nem sammenligning.")
else:
    st.warning("Indtast venligst gyldige tickers (f.eks. AAPL, TSLA) for at generere grafen.")
