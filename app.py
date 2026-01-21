import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Hurtig Aktie-App", layout="wide")

st.title("⚡ Optimeret Aktie-Animation")

tickers = st.sidebar.text_input("Tickers", "MSFT, MSTR")
start_year = st.sidebar.slider("Start år", 2010, 2024, 2015)

if st.button('Hent og vis graf 📈'):
    t_list = [t.strip().upper() for t in tickers.split(",")]
    data = yf.download(t_list, start=f"{start_year}-01-01")['Close']
    data = (data / data.iloc[0]) * 100 

    # Vi laver én hurtig graf i stedet for en hakkende animation
    fig = go.Figure()
    for col in data.columns:
        fig.add_trace(go.Scatter(x=data.index, y=data[col], name=col, mode='lines'))

    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True)) # Her får du en tids-slider i bunden!
    )

    st.plotly_chart(fig, use_container_width=True)
    st.info("Brug slideren i bunden af grafen til at 'spole' gennem tiden. Det lagger ikke!")
