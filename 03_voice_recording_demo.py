# app.py
# ---------------------------------------------
# Streamlit – Quote challenge con registrazione audio, trascrizione, salvataggio Excel e grafico
# Requisiti (nel venv):
#   pip install faster-whisper soundfile openpyxl
# ---------------------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
from faster_whisper import WhisperModel
import soundfile as sf
import io
import hashlib

# ---------- Config & costanti ----------
EXCEL_PATH = Path("quotes.xlsx")
EXCEL_ENGINE = "openpyxl"
PAGE_TITLE = "Movies quotes word counter 🎥"

st.set_page_config(page_title="Quote Challenge", page_icon="🎞️", layout="wide")

# ---------- Stato iniziale ----------
if "last_quote" not in st.session_state:
    st.session_state.last_quote = ""
if "last_wc" not in st.session_state:
    st.session_state.last_wc = 0
if "last_sq" not in st.session_state:
    st.session_state.last_sq = 0
if "last_diff" not in st.session_state:
    st.session_state.last_diff = 0

# stato del widget text_area
if "quote_text" not in st.session_state:
    st.session_state["quote_text"] = ""

# evita trascrizioni duplicate e gestisci prefill asincrono
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "pending_quote" not in st.session_state:
    st.session_state.pending_quote = None

# contatore per rigenerare il widget audio (nuove registrazioni)
if "rec_counter" not in st.session_state:
    st.session_state.rec_counter = 0

# ---------- Funzioni utili ----------
def load_excel(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_excel(path, engine=EXCEL_ENGINE)
        except Exception:
            return pd.DataFrame(columns=["timestamp", "quote", "word_count", "square", "difference"])
    else:
        return pd.DataFrame(columns=["timestamp", "quote", "word_count", "square", "difference"])

def save_excel(df: pd.DataFrame, path: Path) -> None:
    df.to_excel(path, index=False, engine=EXCEL_ENGINE)

def metrics_from_text(text: str):
    clean_text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    wc = len(clean_text.split())
    sq = wc ** 2
    diff = sq - wc
    return wc, sq, diff

@st.cache_resource
def load_stt_model(model_size: str = "tiny"):
    # CPU veloce: quantizzazione int8. Per GPU NVIDIA: device="cuda", compute_type="float16"
    return WhisperModel(model_size, device="cpu", compute_type="int8")

# ---------- Dati & Modello ----------
df = load_excel(EXCEL_PATH)
stt_model = load_stt_model("tiny")

# ---------- HEADER / TESTO ----------
st.title(PAGE_TITLE)
st.write("Conta le parole delle citazioni dei tuoi film preferiti (scrivile o **registrale** con il microfono).")
st.divider()

# ---------- SIDEBAR ----------
st.sidebar.image("blockbuster.png")
st.sidebar.caption("Scrivi una citazione o usane una registrata. Poi premi **Ctrl+Invio** per salvarla.")

# --- Controlli registrazione ---
col_ctrl = st.sidebar.container()
with col_ctrl:
    st.markdown("### 🎙️ Registra una citazione")
    # Bottone per forzare un nuovo widget audio "pulito"
    if st.button("🔄 Nuova registrazione", use_container_width=True):
        st.session_state.rec_counter += 1
        st.session_state.last_audio_hash = None
        st.session_state.pending_quote = None
        st.rerun()

# Widget audio con key dinamica: cambia quando rec_counter cresce
audio_file = st.sidebar.audio_input("Clicca per registrare", key=f"mic_{st.session_state.rec_counter}")

# --- Registrazione & Trascrizione (con anti-loop) ---
if audio_file is not None:
    audio_bytes = audio_file.getvalue()
    st.sidebar.audio(audio_bytes)

    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.last_audio_hash != audio_hash:
        tmp_wav = "temp_input.wav"
        with open(tmp_wav, "wb") as f:
            f.write(audio_bytes)

        try:
            with st.spinner("Trascrivo l'audio..."):
                segments, info = stt_model.transcribe(tmp_wav, language="it", beam_size=1)
                transcript = "".join(seg.text for seg in segments).strip()
        except Exception:
            # fallback: ricodifica un WAV pulito e riprova (max 15s)
            data, samplerate = sf.read(io.BytesIO(audio_bytes))
            max_secs = 15
            if len(data) > samplerate * max_secs:
                data = data[: samplerate * max_secs]
            sf.write(tmp_wav, data, samplerate)
            with st.spinner("Trascrivo l'audio (fallback)..."):
                segments, info = stt_model.transcribe(tmp_wav, language="it", beam_size=1)
                transcript = "".join(seg.text for seg in segments).strip()

        if transcript:
            # metti in pending, segna hash, e prepara subito il widget per una nuova registrazione
            st.session_state.pending_quote = transcript
            st.session_state.last_audio_hash = audio_hash
            st.session_state.rec_counter += 1   # crea un nuovo audio_input vuoto al prossimo run
            st.sidebar.success("Trascrizione completata ✅")
            st.rerun()
        else:
            st.sidebar.info("Nessun parlato rilevato o trascrizione vuota. Riprova con un audio più chiaro.")

# --- Applica l'eventuale testo in pending PRIMA di creare la text_area ---
if st.session_state.pending_quote:
    st.session_state["quote_text"] = st.session_state.pending_quote
    st.session_state.pending_quote = None

# ---------- FORM: Ctrl+Invio = submit ----------
with st.form("quote_form", clear_on_submit=True):
    text_input = st.text_area(
        "Scrivi o registra una Citazione:",
        placeholder="Es. «Houston, abbiamo un problema.» – Apollo 13 (1995)",
        height=120,
        key="quote_text",
    )
    submitted = st.form_submit_button("Aggiungi")

if submitted:
    quote = text_input.strip()
    if quote:
        wc, sq, diff = metrics_from_text(quote)

        st.session_state.last_quote = quote
        st.session_state.last_wc = wc
        st.session_state.last_sq = sq
        st.session_state.last_diff = diff

        new_row = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quote": quote,
            "word_count": wc,
            "square": sq,
            "difference": diff,
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_excel(df, EXCEL_PATH)

        st.success("Quote salvata in 'quotes.xlsx' ✅")
    else:
        st.warning("La citazione è vuota: niente da salvare.")

# ---------- METRICHE ----------
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader(":blue[Parole]")
    st.metric("Word Count", st.session_state.last_wc)
with col2:
    st.subheader(":green[Quadrato]")
    st.metric("Square", st.session_state.last_sq)
with col3:
    st.subheader(":orange[Differenza]")
    st.metric("Difference", st.session_state.last_diff)

st.divider()

# ---------- Tabella dati & Grafico ----------
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
        plot_df = df[["word_count", "square", "difference"]].copy()
        plot_df.index = np.arange(1, len(plot_df) + 1)  # asse X 1..N
        st.line_chart(plot_df, use_container_width=True)
    else:
        missing = 3 - len(df)
        st.info(f"Aggiungi ancora {missing} datapoint{'s' if missing>1 else ''} per vedere il grafico.")

# ---------- Note didattiche ----------
with st.expander("🍿 Come funziona"):
    st.markdown(
        """
- **st.audio_input** mantiene il valore registrato; per registrare di nuovo cambiamo la **key** del widget
  con un contatore (`rec_counter`) o usiamo il bottone **Nuova registrazione**.
- Trascrizione con **Whisper** via `faster-whisper` (modello *tiny* int8 su CPU).
- Anti-loop: hash dell'audio (`last_audio_hash`) per evitare rielaborazioni dello stesso file.
- La citazione trascritta viene caricata nella text area; `clear_on_submit=True` la svuota dopo il salvataggio.
        """
    )
