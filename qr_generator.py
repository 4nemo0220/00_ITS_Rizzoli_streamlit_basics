import streamlit as st
import qrcode
from io import BytesIO

url = "https://chat.whatsapp.com/GvsexvD64qnGu7IRF5xqqk?mode=wwt"
img = qrcode.make(url)
buf = BytesIO()
img.save(buf, format="PNG")

st.image(buf.getvalue())
st.write("Scansiona per partecipare 👉 ", url)