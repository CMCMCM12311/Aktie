import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Aktie-Animator Pro", layout="wide")

st.title("🎬 Aktie-Animator")

# Sidebar til tickers
with st.sidebar:
    st.header("Indstillinger")
    tickers_input = st.text_input("Tickers", "MSFT, MSTR")
    
    st.write("Vælg tidsperiode for animation:")
    col1, col2, col3 = st.columns(3)
    years = 0
    if col1.button("1 år"): years = 1
    if col2.button("5 år"): years = 5
    if col3.button("10 år"): years = 10

# Beregn startdato baseret på knapperne
if years > 0:
    start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
else:
    start_date = "2015-01-01" # Standard hvis ingen knap er trykket

ticker_list = [t.strip().upper() for t in tickers_input.split(",")]

# Hent data
@st.cache_data # Gemmer data så den ikke skal hentes hver gang
def get_data(tickers, start):
    df = yf.download(tickers, start=start)['Close']
    return (df / df.iloc[0]) * 100

try:
    data = get_data(ticker_list, start_date)

    # Byg animationen direkte i Plotly (kører i browseren = intet lag)
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines") for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], title="Dato"),
            yaxis=dict(range=[0, data.max().max() + 50], title="Vækst (Start = 100)"),
            updatemenus=[{
                "type": "buttons",
                "buttons": [{
                    "label": "Afspil Udvikling 🚀",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 20, "redraw": True}, "fromcurrent": True}]
                }]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), 10)] # Vi tager hver 10. dag for flydende bevægelse
    )

    fig.update_layout(template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Indtast tickers og vælg en periode for at starte.")

st.info("Tryk på 'Afspil Udvikling' i grafen for at se animationen uden lagg.")
