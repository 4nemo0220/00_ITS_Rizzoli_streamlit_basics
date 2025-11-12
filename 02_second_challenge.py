import streamlit as st
import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime

# *CONSTANTS
EXCEL_PATH = Path("quotes.xlsx")
EXCEL_ENGINE = "openpyxl"  # assicura scrittura xlsx su Windows

st.set_page_config(page_title="Quote Challenge", page_icon="🎞️", layout="wide")

# *STATE CONFIG
if "last_quote" not in st.session_state:
    st.session_state.last_quote = ""
if "last_wc" not in st.session_state:
    st.session_state.last_wc = 0
if "last_pw" not in st.session_state:
    st.session_state.last_pw = 0
if "last_diff" not in st.session_state:
    st.session_state.last_diff = 0

# *UTILS
def load_excel(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_excel(path, engine=EXCEL_ENGINE)
        except Exception:
            # if exception init new file
            return pd.DataFrame(columns=["timestamp", "quote", "word_count", "power", "difference"])
    else:
        return pd.DataFrame(columns=["timestamp", "quote", "word_count", "power", "difference"])

def save_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False, engine=EXCEL_ENGINE)

def metrics_from_text(text: str, number):
    # Count logic
    clean_text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    wc = len(clean_text.split())
    pw = wc ** number
    diff = pw - wc
    return wc, pw, diff

# *DATASET LOADING
df = load_excel(EXCEL_PATH)

# *HEADER
st.title("Movies quotes word counter 🎥")
st.write("Conta le parole delle citazioni dei tuoi film preferiti")
st.divider()

# *SIDEBAR
st.sidebar.image("blockbuster.png")  
st.sidebar.caption("Scrivi una citazione e premi **Ctrl+Invio** per salvarla.")

# *FORM
number = st.slider("Scegli un numero:", 1, 10, 5)
with st.form("quote_form", clear_on_submit=True):
    text_input = st.text_area(
        "Scrivi una Citazione:",
        placeholder="Poiché qualcosa pensa diversamente da noi, vuol forse dire che non sta pensando?\nAlan Turing - The Imitation Game",
        height=120,
    )
    submitted = st.form_submit_button("Aggiungi")

if submitted:
    quote = text_input.strip()
    if quote:
        wc, pw, diff = metrics_from_text(quote, number)
        # Update state with last entry
        st.session_state.last_quote = quote
        st.session_state.last_wc = wc
        st.session_state.last_pw = pw
        st.session_state.last_diff = diff

        # Save in df
        new_row = pd.DataFrame(
            [{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "quote": quote,
                "word_count": wc,
                "square": pw,
                "difference": diff,
            }]
        )
        df = pd.concat([df, new_row], ignore_index=True)
        save_excel(df, EXCEL_PATH)
        st.success("Quote salvata in 'quotes.xlsx' ✅")
    else:
        st.warning("La citazione è vuota: niente da salvare.")

# *METRICS
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(":blue[Parole]")
    st.metric("Word Count", st.session_state.last_wc)
with col2:
    st.subheader(":green[Quadrato]")
    st.metric("Square", st.session_state.last_pw)
with col3:
    st.subheader(":orange[Differenza]")
    st.metric("Difference", st.session_state.last_diff)

st.divider()

# *TABLE & LINECHART
left, right = st.columns([1, 1])

with left:
    st.subheader("📄 Log citazioni")
    if df.empty:
        st.info("Nessun dato ancora. Aggiungi una quote con **Ctrl+Invio**.")
    else:
        st.dataframe(df, use_container_width=True, height=260)

with right:
    st.subheader("📈 Trend")
    if len(df) >= 3:
        plot_df = df[["word_count", "square", "difference"]]
        # usa l’indice come asse x (1..N) per semplicità didattica
        plot_df.index = np.arange(1, len(plot_df) + 1)
        st.line_chart(plot_df, use_container_width=True)
    else:
        missing = 3 - len(df)
        st.info(f"Aggiungi ancora {missing} datapoint{'s' if missing>1 else ''} per vedere il grafico.")

# * EDU NOTES
with st.expander("🍿 Come funziona"):
    st.markdown(
        """
- **Ctrl+Invio** nella form invia i dati senza cliccare il bottone.
- Ad ogni submit, aggiungiamo una riga a `quotes.xlsx` con: *quote, word_count, square, difference*.
- Le metriche mostrano **l'ultimo inserimento**.
- Il grafico appare quando ci sono **≥ 3 righe** nel file.
- Se vuoi ripartire da zero, elimina `quotes.xlsx` (o spostalo).
        """
    )