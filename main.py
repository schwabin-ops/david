
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="DAVID Finance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

URL = "https://david-ai-arjg.onrender.com/finance"

st.markdown("""
<style>
    #MainMenu, footer, header {
        visibility: hidden;
    }

    .stApp {
        margin: 0;
        padding: 0;
    }

    .block-container {
        max-width: 100%;
        padding: 0 !important;
        margin: 0 !important;
    }

    iframe {
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

components.iframe(
    URL,
    height=1100,
    scrolling=True
)
