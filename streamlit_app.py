import streamlit as st

st.set_page_config(
    page_title="EV Analytics & Prediction",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Electric Vehicle Analytics & Prediction System")
st.markdown("""
### Welcome to the EV Data Intelligence Platform

This system triangulates data from multiple sources to predict EV specifications and costs.

**Navigate using the sidebar:**
- 📈 **Market Insights**: Explore EV market trends and comparisons.
- 🧪 **Model Training Lab**: Train and evaluate prediction models (Fixes applied: No data leakage).
- 🔮 **Real-Time Prediction**: Predict EV range based on specifications (Fixes applied: Crash prevention).
""")

st.info("👈 Select a page from the sidebar to begin")
