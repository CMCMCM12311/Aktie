import streamlit as st
import yfinance as yf
import plotly.express as px
import time

# Gør siden bred og mørk
st.set_page_config(page_title="Aktie-Expert", layout="wide", initial_sidebar_state="expanded")

st.title("🚀 Aktie-Rejsen: MSFT vs MSTR")

# Sidebar med lidt mere info
with st.sidebar:
    st.header("Konfiguration")
    tickers = st.text_input("Vælg Tickers", "MSFT, MSTR")
    speed = st.slider("Animationshastighed", 0.01, 0.2, 0.05)
    
st.info("I 2018 begyndte dynamikken at ændre sig. Prøv at trykke Play og hold øje med de to linjer!")

if st.button('Kør Animation'):
    t_list = [t.strip().upper() for t in tickers.split(",")]
    data = yf.download(t_list, start="2015-01-01")['Close']
    data = (data / data.iloc[0]) * 100 # Normalisering
    
    placeholder = st.empty()
    
    for i in range(5, len(data), 10):
        curr = data.iloc[:i].reset_index().melt(id_vars='Date')
        fig = px.line(curr, x='Date', y='value', color='Ticker', template="plotly_dark")
        fig.update_layout(yaxis_title="Vækst i % (Start = 100)")
        placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(speed)
