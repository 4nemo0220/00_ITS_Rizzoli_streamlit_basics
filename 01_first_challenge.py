# Import necessary packages
import streamlit as st
import re


# *UTILITY
def metrics_from_text(text: str, number):
    # Count logic
    clean_text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    wc = len(clean_text.split())
    pw = wc ** number
    diff = pw - wc
    return wc, pw, diff

# *TEXT ELEMENTS
st.title("Movies quotes word counter 🎥")
st.write("Conta le parole delle citazioni dei tuoi film preferiti")

# *WIDGETS
st.divider()
# Slider
number = st.slider("Scegli un numero:", 1, 10, 2)

# *SIDEBAR
st.sidebar.title(":blue[**Alan Turing**]")
st.sidebar.image("Alan_Turing_pic.jpg")
st.sidebar.divider()
st.sidebar.caption("Scrivi una citazione e premi **Ctrl+Invio** per salvarla.")

# *FORM
with st.form("quote_form", clear_on_submit=True):
    text_input = st.text_area(
        "Scrivi una Citazione:",
        placeholder="Poiché qualcosa pensa diversamente da noi, vuol forse dire che non sta pensando?\nAlan Turing - The Imitation Game",
        height=120,
    )
    submitted = st.form_submit_button("Aggiungi")

wc, pw, diff = metrics_from_text(text_input, number)

if submitted:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(":blue[Numero scelto]")
        st.metric("Word count", wc)

    with col2:
        st.subheader(":green[Potenza]")
        st.metric("Power", pw)

    with col3:
        st.subheader(":red[Scarto]")
        st.metric("Difference", diff)