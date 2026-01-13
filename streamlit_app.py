import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="Intelligent EV Analytics V3", page_icon="⚡", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00FF99; font-family: 'Segoe UI', sans-serif;}
    .stMetric {background-color: #262730; border: 1px solid #444;}
    </style>""", unsafe_allow_html=True)

st.title("⚡ Intelligent EV Analytics: The Master Portal")
st.markdown("### 🧬 Tri-Dataset Architecture: Market + Physics + Prices")

# --- ROBUST DATA LOADER (V3.2) ---
@st.cache_data
def load_and_process_data():
    def load_csv(zip_name):
        try:
            with zipfile.ZipFile(zip_name, "r") as z:
                files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f]
                return pd.read_csv(z.open(max(files, key=len))) if files else None
        except: return None

    try:
        # 1. LOAD RAW DATA
        df_m = load_csv("raw_data.zip")   # Market
        df_s = load_csv("specs_data.zip") # Specs
        df_p = load_csv("prices_data.zip") # Prices

        if df_m is None or df_s is None or df_p is None:
            raise ValueError("One or more zip files could not be loaded.")

        # 2. PREPARE MARKET DATA (Dataset A)
        df_m['join_make'] = df_m['Make'].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m['Model'].astype(str).str.lower().str.strip()

        # 3. PREPARE SPECS DATA (Dataset B)
        s_make = next(c for c in df_s.columns if c.lower() in ['brand', 'make'])
        s_model = next(c for c in df_s.columns if c.lower() in ['model', 'model_name'])
        df_s['join_make'] = df_s[s_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[s_model].astype(str).str.lower().str.strip()

        # 4. PREPARE PRICES DATA (Dataset C)
        if 'Car_name' in df_p.columns:
            split_data = df_p['Car_name'].astype(str).str.split(' ', n=1, expand=True)
            df_p['join_make'] = split_data[0].str.lower().str.strip()
            df_p['join_model'] = split_data[1].str.lower().str.strip() if len(split_data.columns) > 1 else ""
        else:
            p_make = next(c for c in df_p.columns if c.lower() in ['brand', 'make'])
            p_model = next(c for c in df_p.columns if c.lower() in ['model', 'model_name'])
            df_p['join_make'] = df_p[p_make].astype(str).str.lower().str.strip()
            df_p['join_model'] = df_p[p_model].astype(str).str.lower().str.strip()

        # 5. MERGE PIPELINE
        # Merge 1: Market + Specs (for Physics Analysis)
        df_step1 = pd.merge(df_m, df_s, on=['join_make', 'join_model'], how='inner')
        # Merge 2: Result + Prices (for Economics Analysis)
        df_final = pd.merge(df_step1, df_p, on=['join_make', 'join_model'], how='inner')

        # 6. CLEANUP
        # Fix Price
        price_col = next((c for c in df_final.columns if 'price' in c.lower()), None)
        if price_col:
            if df_final[price_col].dtype == object:
                df_final[price_col] = df_final[price_col].astype(str).str.replace('.', '', regex=False)
            df_final['Final_Price_USD'] = pd.to_numeric(df_final[price_col], errors='coerce') * 1.09
        else:
            df_final['Final_Price_USD'] = 50000

        # Fix Range
        range_col = next((c for c in df_s.columns if 'range' in c.lower()), None)
        if range_col:
            df_final['Final_Range_Miles'] = df_final[range_col] * 0.621371
            df_final = df_final[df_final['Final_Range_Miles'] > 10]

        # RETURN 3 THINGS NOW: Final Merged, Specs, AND Raw Market Data
        return df_final, df_specs, df_m

    except Exception as e:
        st.error(f"🛑 Critical Data Error: {e}")
        return None, None, None

# --- APP LOGIC ---
if 'df_main' not in st.session_state:
    with st.spinner("Processing Tri-Dataset Pipeline..."):
        # Unpack 3 values
        df_final, df_specs, df_market_raw = load_and_process_data()
        
        if df_final is not None:
            st.session_state['df_main'] = df_final        # The tiny strict merged data (For Prediction)
            st.session_state['df_specs'] = df_specs       # Specs cols
            st.session_state['df_market_raw'] = df_market_raw # The HUGE raw data (For Insights)
            st.rerun()

if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Vehicles (Fully Matched)", len(df))
    c2.metric("Avg Range", f"{df['Final_Range_Miles'].mean():.0f} mi")
    c3.metric("Avg Price", f"${df['Final_Price_USD'].mean():,.0f}")
    
    st.success("✅ System Ready. Go to 'Market Insights' to see the full data.")
