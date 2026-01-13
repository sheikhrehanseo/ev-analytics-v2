import streamlit as st
import pandas as pd
import numpy as np
import os
import zipfile

# --- PAGE CONFIG ---
st.set_page_config(page_title="Intelligent EV Analytics V4", page_icon="⚡", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00FF99; font-family: 'Segoe UI', sans-serif;}
    </style>""", unsafe_allow_html=True)

st.title("⚡ Intelligent EV Analytics: API Live Pipeline")
st.markdown("### 🧬 Tri-Dataset Architecture: Market + Physics + Prices (Live from Kaggle)")

# --- 1. KAGGLE AUTHENTICATION & DOWNLOADER ---
def authenticate_kaggle():
    # Check if secrets exist
    if 'kaggle' in st.secrets:
        os.environ['KAGGLE_USERNAME'] = st.secrets['kaggle']['username']
        os.environ['KAGGLE_KEY'] = st.secrets['kaggle']['key']
    else:
        st.error("❌ Kaggle credentials not found in secrets!")
        st.stop()

@st.cache_resource # Cache this so we don't redownload on every click
def download_datasets():
    authenticate_kaggle()
    from kaggle.api.kaggle_api_extended import KaggleApi
    api = KaggleApi()
    api.authenticate()

    # Define Datasets (User/Dataset-Name)
    datasets = {
        "raw_data.zip": "ricardobj/electric-vehicle-population",
        "specs_data.zip": "urvishahir/electric-vehicle-specifications-dataset-2025",
        "prices_data.zip": "fatihilhan/electric-vehicle-specifications-and-prices"
    }

    # Download Loop
    for filename, kaggle_ref in datasets.items():
        if not os.path.exists(filename):
            with st.spinner(f"⬇️ Downloading {kaggle_ref}..."):
                api.dataset_download_files(kaggle_ref, path=".", unzip=False)
                # Rename the default 'archive.zip' or specific name to our standard name
                # Kaggle saves it as the dataset name usually, let's just rename the zip file found
                # Actually, Kaggle API downloads exactly the zip file name.
                # Simplification: We just rename whatever was downloaded to our standard name
                # BUT: The API downloads as 'electric-vehicle-population.zip'. 
                # To be safe, we will just rename the file that appears.
                
                # Check what file was created
                downloaded_file = kaggle_ref.split('/')[-1] + ".zip"
                if os.path.exists(downloaded_file):
                    os.rename(downloaded_file, filename)
    
    return True

# --- 2. DATA PROCESSING (Same logic as V3.3) ---
@st.cache_data
def load_and_process_data():
    def load_csv(zip_name):
        try:
            with zipfile.ZipFile(zip_name, "r") as z:
                files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f]
                return pd.read_csv(z.open(max(files, key=len))) if files else None
        except: return None

    try:
        # Load Raw
        df_m = load_csv("raw_data.zip")
        df_s = load_csv("specs_data.zip")
        df_p = load_csv("prices_data.zip")

        if df_m is None or df_s is None or df_p is None:
            raise ValueError("Download failed or zips are empty.")

        # Prepare Keys
        df_m['join_make'] = df_m['Make'].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m['Model'].astype(str).str.lower().str.strip()

        s_make = next(c for c in df_s.columns if c.lower() in ['brand', 'make'])
        s_model = next(c for c in df_s.columns if c.lower() in ['model', 'model_name'])
        df_s['join_make'] = df_s[s_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[s_model].astype(str).str.lower().str.strip()

        if 'Car_name' in df_p.columns:
            split_data = df_p['Car_name'].astype(str).str.split(' ', n=1, expand=True)
            df_p['join_make'] = split_data[0].str.lower().str.strip()
            df_p['join_model'] = split_data[1].str.lower().str.strip() if len(split_data.columns) > 1 else ""
        else:
            p_make = next(c for c in df_p.columns if c.lower() in ['brand', 'make'])
            p_model = next(c for c in df_p.columns if c.lower() in ['model', 'model_name'])
            df_p['join_make'] = df_p[p_make].astype(str).str.lower().str.strip()
            df_p['join_model'] = df_p[p_model].astype(str).str.lower().str.strip()

        # Merge
        df_step1 = pd.merge(df_m, df_s, on=['join_make', 'join_model'], how='inner')
        df_final = pd.merge(df_step1, df_p, on=['join_make', 'join_model'], how='inner')

        # Cleanup
        price_col = next((c for c in df_final.columns if 'price' in c.lower()), None)
        if price_col:
            if df_final[price_col].dtype == object:
                df_final[price_col] = df_final[price_col].astype(str).str.replace('.', '', regex=False)
            df_final['Final_Price_USD'] = pd.to_numeric(df_final[price_col], errors='coerce') * 1.09
        else:
            df_final['Final_Price_USD'] = 50000

        range_col = next((c for c in df_s.columns if 'range' in c.lower()), None)
        if range_col:
            df_final['Final_Range_Miles'] = df_final[range_col] * 0.621371
            df_final = df_final[df_final['Final_Range_Miles'] > 10]

        return df_final, df_s, df_m

    except Exception as e:
        st.error(f"Data Error: {e}")
        return None, None, None

# --- EXECUTION FLOW ---
if 'df_main' not in st.session_state:
    # 1. Trigger Download
    if download_datasets():
        # 2. Trigger Processing
        with st.spinner("Processing Data..."):
            df_final, df_specs, df_market_raw = load_and_process_data()
            
            if df_final is not None:
                st.session_state['df_main'] = df_final
                st.session_state['df_specs'] = df_specs
                st.session_state['df_market_raw'] = df_market_raw
                st.rerun()

# --- METRICS UI ---
if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Vehicles", len(df))
    c2.metric("Avg Range", f"{df['Final_Range_Miles'].mean():.0f} mi")
    c3.metric("Avg Price", f"${df['Final_Price_USD'].mean():,.0f}")
    st.success("✅ Kaggle API Connected & Data Loaded.")
