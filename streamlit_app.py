import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import os

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

# --- ROBUST DATA LOADER ---
@st.cache_data
def load_and_process_data():
    # Helper: Load largest CSV from Zip
    def load_largest_csv(zip_name):
        try:
            with zipfile.ZipFile(zip_name, "r") as z:
                csv_files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f]
                if not csv_files: return None
                largest = max(csv_files, key=lambda x: z.getinfo(x).file_size)
                return pd.read_csv(z.open(largest))
        except: return None

    # Helper: Find column safely
    def find_col(df, candidates, dataset_name):
        # lower case check
        for col in df.columns:
            if col.lower().strip() in candidates:
                return col
        # If failed, raise error with details
        raise ValueError(f"Could not find {candidates} in {dataset_name}. Found: {list(df.columns)}")

    try:
        # 1. LOAD FILES
        df_m = load_largest_csv("raw_data.zip")
        df_s = load_largest_csv("specs_data.zip")
        df_p = load_largest_csv("prices_data.zip")

        if df_m is None: raise ValueError("Failed to load raw_data.zip")
        if df_s is None: raise ValueError("Failed to load specs_data.zip")
        if df_p is None: raise ValueError("Failed to load prices_data.zip")

        # 2. NORMALIZE KEYS (LOWERCASE)
        # Market Data (A)
        m_make = find_col(df_m, ['make', 'brand', 'manufacturer'], "Dataset A (Market)")
        m_model = find_col(df_m, ['model', 'vehicle'], "Dataset A (Market)")
        df_m['join_make'] = df_m[m_make].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m[m_model].astype(str).str.lower().str.strip()

        # Specs Data (B)
        s_make = find_col(df_s, ['brand', 'make', 'manufacturer'], "Dataset B (Specs)")
        s_model = find_col(df_s, ['model', 'model_name', 'vehicle'], "Dataset B (Specs)")
        df_s['join_make'] = df_s[s_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[s_model].astype(str).str.lower().str.strip()

        # Prices Data (C)
        p_make = find_col(df_p, ['brand', 'make', 'car_name'], "Dataset C (Prices)")
        p_model = find_col(df_p, ['model', 'model_name', 'vehicle'], "Dataset C (Prices)")
        df_p['join_make'] = df_p[p_make].astype(str).str.lower().str.strip()
        df_p['join_model'] = df_p[p_model].astype(str).str.lower().str.strip()

        # 3. MERGE
        df_step1 = pd.merge(df_m, df_s, on=['join_make', 'join_model'], how='inner')
        df_final = pd.merge(df_step1, df_p, on=['join_make', 'join_model'], how='inner')

        # 4. CLEANUP
        # Price (Try to find 'price' or 'msrp')
        price_cols = [c for c in df_final.columns if 'price' in c.lower() or 'msrp' in c.lower()]
        if price_cols:
            # Pick the first one found
            df_final['Final_Price_USD'] = df_final[price_cols[0]] * 1.1 # Approx Euro->USD
        else:
            df_final['Final_Price_USD'] = 50000 # Fallback default

        # Range (Try to find 'range')
        range_cols = [c for c in df_s.columns if 'range' in c.lower()]
        if range_cols:
            df_final['Final_Range_Miles'] = df_final[range_cols[0]] * 0.621371
            df_final = df_final[df_final['Final_Range_Miles'] > 10]
        else:
            raise ValueError("No 'Range' column found in Specs data.")

        return df_final, df_s

    except Exception as e:
        st.error(f"🛑 Data Processing Failed: {e}")
        return None, None

# Run Loader
if 'df_main' not in st.session_state:
    with st.spinner("Initializing Tri-Dataset Pipeline..."):
        df_final, df_specs = load_and_process_data()
        
        if df_final is not None:
            st.session_state['df_main'] = df_final
            st.session_state['df_specs'] = df_specs
            st.success("✅ Data Pipeline Initialized!")
            st.rerun()
        else:
            st.stop()

# --- METRICS ---
if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    
    if len(df) == 0:
        st.error("⚠️ Merge resulted in 0 rows. Check if 'Make/Model' names match (e.g. 'Tesla' vs 'TESLA').")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Vehicles", len(df))
        c2.metric("Avg Range", f"{df['Final_Range_Miles'].mean():.0f} mi")
        c3.metric("Avg Price", f"${df['Final_Price_USD'].mean():,.0f}")
        
        st.info("👈 Select a module from the sidebar to begin.")
