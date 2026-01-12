import streamlit as st
import pandas as pd
import numpy as np
import zipfile

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Intelligent EV Analytics V3",
    page_icon="⚡",
    layout="wide"
)

# --- GLOBAL STYLING ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00FF99; font-family: 'Segoe UI', sans-serif;}
    .stButton>button {background-color: #00FF99; color: black; font-weight: bold; width: 100%;}
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Intelligent EV Analytics: The Master Portal")
st.markdown("### 🧬 Tri-Dataset Architecture: Market + Physics + Prices")

# --- DATA LOADING ENGINE ---
@st.cache_data
def load_and_process_data():
    try:
        # 1. LOAD DATASET A (Market - raw_data.csv)
        with zipfile.ZipFile("raw_data.zip", "r") as z:
            # We explicitly look for raw_data.csv as per your instruction
            df_m = pd.read_csv(z.open("raw_data.csv"))

        # 2. LOAD DATASET B (Specs - specs_data.csv)
        with zipfile.ZipFile("specs_data.zip", "r") as z:
            df_s = pd.read_csv(z.open("specs_data.csv"))

        # 3. LOAD DATASET C (Prices - prices_data.csv)
        with zipfile.ZipFile("prices_data.zip", "r") as z:
            df_p = pd.read_csv(z.open("prices_data.csv"))

        # --- NORMALIZE KEYS (LOWERCASE) ---
        # Dataset A
        df_m['join_make'] = df_m['Make'].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m['Model'].astype(str).str.lower().str.strip()
        
        # Dataset B (Dynamic Column Search)
        b_make = next(c for c in df_s.columns if c.lower() in ['brand', 'make'])
        b_model = next(c for c in df_s.columns if c.lower() in ['model', 'model_name'])
        df_s['join_make'] = df_s[b_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[b_model].astype(str).str.lower().str.strip()
        
        # Dataset C (Dynamic Column Search)
        c_make = next(c for c in df_p.columns if c.lower() in ['brand', 'make'])
        c_model = next(c for c in df_p.columns if c.lower() in ['model', 'model_name'])
        df_p['join_make'] = df_p[c_make].astype(str).str.lower().str.strip()
        df_p['join_model'] = df_p[c_model].astype(str).str.lower().str.strip()

        # --- MERGE LOGIC ---
        # Merge 1: Market + Specs
        df_step1 = pd.merge(df_m, df_s, on=['join_make', 'join_model'], how='inner')
        
        # Merge 2: Result + Prices
        df_final = pd.merge(df_step1, df_p, on=['join_make', 'join_model'], how='inner')

        # --- CLEANUP & CONVERSIONS ---
        # 1. Price Conversion (Euro -> USD approx 1.1)
        price_col = next((c for c in df_final.columns if 'price' in c.lower()), None)
        if price_col:
            df_final['Final_Price_USD'] = df_final[price_col] * 1.1
            
        # 2. Range Conversion (KM -> Miles)
        range_col = next((c for c in df_s.columns if 'range' in c.lower()), None)
        if range_col:
            df_final['Final_Range_Miles'] = df_final[range_col] * 0.621371
            # Filter valid ranges
            df_final = df_final[df_final['Final_Range_Miles'] > 10]

        return df_final, df_s  # Return merged data AND specs (for column referencing)

    except Exception as e:
        st.error(f"Data Loading Error: {e}")
        return None, None

# Run Loader
if 'df_main' not in st.session_state:
    with st.spinner("Initializing Tri-Dataset Pipeline..."):
        df_final, df_specs = load_and_process_data()
        
        if df_final is not None:
            st.session_state['df_main'] = df_final
            st.session_state['df_specs'] = df_specs # Saved for column names
            st.success("✅ Data Pipeline Initialized Successfully!")
        else:
            st.stop()

# --- LANDING PAGE METRICS ---
if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Vehicles Analyzed", len(df))
    c2.metric("Avg Range (Miles)", f"{df['Final_Range_Miles'].mean():.0f}")
    c3.metric("Avg Price (USD)", f"${df['Final_Price_USD'].mean():,.0f}")
    
    st.info("👈 Select a module from the sidebar to begin analysis.")
