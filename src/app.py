"""Streamlit multi-page navigation hub."""

import streamlit as st

st.set_page_config(
    page_title="Eco-Chat",
    page_icon="📊",
    layout="wide",
)

home = st.Page("pages/home.py", title="Home", default=True)
chat = st.Page("pages/chat.py", title="Chat")

nav = st.navigation([home, chat], position="hidden")
nav.run()
