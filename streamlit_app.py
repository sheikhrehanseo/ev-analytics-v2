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

# --- UNIVERSAL DATA LOADER ---
@st.cache_data
def load_and_process_data():
    # Helper to find the largest CSV in a zip (ignoring name mismatches)
    def load_largest_csv_from_zip(zip_name):
        try:
            with zipfile.ZipFile(zip_name, "r") as z:
                # Find all CSVs (ignore MACOSX garbage)
                csv_files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f]
                
                if not csv_files:
                    st.error(f"❌ Error: No CSV file found inside {zip_name}")
                    return None
                
                # Pick the largest file (safest bet for data)
                largest_csv = max(csv_files, key=lambda x: z.getinfo(x).file_size)
                return pd.read_csv(z.open(largest_csv))
        except FileNotFoundError:
            st.error(f"❌ Error: Could not find {zip_name} in your repository.")
            return None
        except Exception as e:
            st.error(f"❌ Error reading {zip_name}: {e}")
            return None

    # 1. LOAD DATASETS (Auto-Detect)
    df_m = load_largest_csv_from_zip("raw_data.zip")
    df_s = load_largest_csv_from_zip("specs_data.zip")
    df_p = load_largest_csv_from_zip("prices_data.zip")

    # Stop if any load failed
    if df_m is None or df_s is None or df_p is None:
        return None, None

    try:
        # --- NORMALIZE KEYS (LOWERCASE) ---
        # Dataset A (Market)
        df_m['join_make'] = df_m['Make'].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m['Model'].astype(str).str.lower().str.strip()
        
        # Dataset B (Specs)
        b_make = next(c for c in df_s.columns if c.lower() in ['brand', 'make'])
        b_model = next(c for c in df_s.columns if c.lower() in ['model', 'model_name'])
        df_s['join_make'] = df_s[b_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[b_model].astype(str).str.lower().str.strip()
        
        # Dataset C (Prices)
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

        return df_final, df_s

    except Exception as e:
        st.error(f"🛑 Merge Error: {e}")
        return None, None

# Run Loader
if 'df_main' not in st.session_state:
    with st.spinner("Initializing Tri-Dataset Pipeline..."):
        df_final, df_specs = load_and_process_data()
        
        if df_final is not None:
            st.session_state['df_main'] = df_final
            st.session_state['df_specs'] = df_specs
            st.success("✅ Data Pipeline Initialized Successfully!")
            st.rerun()
        else:
            st.stop()

# --- LANDING PAGE METRICS ---
if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    
    if len(df) == 0:
        st.error("⚠️ The Merge resulted in 0 rows. Please check that 'Make' and 'Model' spellings match between your datasets.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Vehicles Analyzed", len(df))
        c2.metric("Avg Range (Miles)", f"{df['Final_Range_Miles'].mean():.0f}")
        c3.metric("Avg Price (USD)", f"${df['Final_Price_USD'].mean():,.0f}")
        
        st.info("👈 Select a module from the sidebar (Market Insights, Model Lab, or Predictor) to begin.")
