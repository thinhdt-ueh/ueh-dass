"""Renders the shared footer.html at the bottom of every page."""
import os

import streamlit as st

FOOTER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "footer.html")


def render_footer():
    if os.path.exists(FOOTER_PATH):
        with open(FOOTER_PATH, encoding="utf-8") as f:
            st.markdown(f.read(), unsafe_allow_html=True)
