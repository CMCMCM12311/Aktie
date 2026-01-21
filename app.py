import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Konfiguration
st.set_page_config(page_title="Aktie-Animator Pro", layout="wide", initial_sidebar_state="collapsed")

st.title("🎬 Aktie-Animator")

# --- SESSION STATE (HUSKER DINE VALG) ---
if 'tickers_val' not in st.session_state:
    st.session_state.tickers_val = "MSFT, MSTR"
if 'years_val' not in st.session_state:
    st.session_state.years_val = 10  # Standard er nu 10 år

# --- DATA HENTNING ---
ticker_list = [t.strip().upper() for t in st.session_state.tickers_val.split(",")]

# Beregn startdato (200 år er 'Børsnotering' i praksis)
if st.session_state.years_val == "IPO":
    start_date = "1900-01-01" 
else:
    start_date = (datetime.now() - timedelta(days=st.session_state.years_val*365)).strftime('%Y-%m-%d')

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

# --- GRAF SEKTION (AUTO-PLAY) ---
if data is not None:
    fig = go.Figure(
        data=[go.Scatter(x=[data.index[0]], y=[data[c].iloc[0]], name=c, mode="lines") for c in data.columns],
        layout=go.Layout(
            xaxis=dict(range=[data.index.min(), data.index.max()], title="Dato"),
            yaxis=dict(title="Vækst (Start = 100)"),
            height=600,
            template="plotly_dark",
            hovermode="x unified",
            # Her aktiverer vi auto-play ved load
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "visible": False, # Skjuler knapperne helt
                "buttons": [{
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": 10, "redraw": True}, "fromcurrent": True, "mode": "immediate"}]
                }]
            }]
        ),
        frames=[go.Frame(data=[go.Scatter(x=data.index[:i], y=data[c].iloc[:i]) for c in data.columns]) 
                for i in range(1, len(data), 15)] # Hver 15. dag for hurtig/glat animation
    )

    # Denne lille stump kode trigger animationen automatisk
    fig.update_layout(
        xaxis=dict(autorange=False),
        yaxis=dict(autorange=True)
    )
    
    # Vis grafen og kør animationen med det samme
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Trigger auto-animation via JavaScript (Streamlit hack for automatisk start)
    st.components.v1.html(
        """
        <script>
        var checkExist = setInterval(function() {
           var playBtn = window.parent.document.querySelector('rect.updatemenu-button-rect');
           if (playBtn) {
              playBtn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
              clearInterval(checkExist);
           }
        }, 100);
        </script>
        """,
        height=0,
    )
else:
    st.error("Kunne ikke hente data. Tjek tickers.")

# --- KONTROLPANEL (NEDENUNDER) ---
st.write("---")
col1, col2 = st.columns([2, 3])

with col1:
    new_tickers = st.text_input("Tickers (f.eks. NVDA, AAPL, BTC-USD)", value=st.session_state.tickers_val)
    if new_tickers != st.session_state.tickers_val:
        st.session_state.tickers_val = new_tickers
        st.rerun()

with col2:
    st.write("Skift tidshorisont (starter animation med det samme):")
    t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
    
    if t_col1.button("1 år"): 
        st.session_state.years_val = 1
        st.rerun()
    if t_col2.button("5 år"): 
        st.session_state.years_val = 5
        st.rerun()
    if t_col3.button("10 år"): 
        st.session_state.years_val = 10
        st.rerun()
    if t_col4.button("20 år"): 
        st.session_state.years_val = 20
        st.rerun()
    if t_col5.button("Børsnotering 🏛️"): 
        st.session_state.years_val = "IPO"
        st.rerun()

st.caption(f"Viser nu: {st.session_state.tickers_val}. Periode: {st.session_state.years_val if st.session_state.years_val != 'IPO' else 'Max historik'} år.")
