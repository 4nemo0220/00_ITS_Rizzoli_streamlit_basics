# Import necessary packages
import streamlit as st
import re

# *TEXT ELEMENTS
# App title
st.title("Hello World! 🌍")
# Header
st.header("Questa è la mia prima streamlit app :streamlit:")
# Content
st.write("Questa è un’app interattiva per la visualizzazione dei dati")

# *WIDGETS
st.divider()
# Slider
number = st.slider("Scegli un numero:", 1, 10, 5)

# *SIDEBAR
st.sidebar.title(":blue[**Parametri**]")

text_input = st.text_area("Scrivi una Citazione:", placeholder=f"Poiché qualcosa pensa diversamente da noi, vuol forse dire che non sta pensando? \nAlan Turing - The imitation game") 

clean_text = re.sub(r'[^\w\s]', '', text_input)
word_count = len(clean_text.split())
number = word_count

col1, col2 = st.columns(2)

with col1:
    st.subheader(":blue[Numero scelto]")
    st.write(number)

with col2:
    st.subheader(":green[Quadrato del numero]")
    st.write(number**2)