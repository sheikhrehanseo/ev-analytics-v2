import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Intelligent EV Analytics V5", page_icon="⚡", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1, h2, h3 {color: #00FF99; font-family: 'Segoe UI', sans-serif;}
    .stMetric {background-color: #262730; border: 1px solid #444;}
    </style>""", unsafe_allow_html=True)

st.title("⚡ Intelligent EV Analytics: The Master Portal")
st.markdown("### 🧬 Tri-Dataset Architecture: Market + Physics + Prices (Smart Match)")

# --- 1. KAGGLE DOWNLOADER ---
def authenticate_kaggle():
    if 'kaggle' in st.secrets:
        os.environ['KAGGLE_USERNAME'] = st.secrets['kaggle']['username']
        os.environ['KAGGLE_KEY'] = st.secrets['kaggle']['key']

@st.cache_resource
def download_datasets():
    # Only run if files are missing
    if os.path.exists("raw_data.zip") and os.path.exists("specs_data.zip") and os.path.exists("prices_data.zip"):
        return True
        
    authenticate_kaggle()
    from kaggle.api.kaggle_api_extended import KaggleApi
    try:
        api = KaggleApi()
        api.authenticate()
        datasets = {
            "raw_data.zip": "ricardobj/electric-vehicle-population",
            "specs_data.zip": "urvishahir/electric-vehicle-specifications-dataset-2025",
            "prices_data.zip": "fatihilhan/electric-vehicle-specifications-and-prices"
        }
        for fname, ref in datasets.items():
            if not os.path.exists(fname):
                with st.spinner(f"⬇️ Downloading {ref}..."):
                    api.dataset_download_files(ref, path=".", unzip=False)
                    # Find the newest zip file and rename it
                    files = [f for f in os.listdir('.') if f.endswith('.zip')]
                    newest = max(files, key=os.path.getctime)
                    if newest != fname:
                        if os.path.exists(fname): os.remove(fname)
                        os.rename(newest, fname)
        return True
    except Exception as e:
        st.error(f"Kaggle API Error: {e}")
        return False

# --- 2. DATA PROCESSING (SMART MATCH LOGIC) ---
@st.cache_data
def load_and_process_data():
    def load_csv(zip_name):
        try:
            with zipfile.ZipFile(zip_name, "r") as z:
                # Find valid CSV (ignore MACOSX)
                files = [f for f in z.namelist() if f.endswith('.csv') and '__MACOSX' not in f]
                return pd.read_csv(z.open(max(files, key=len))) if files else None
        except: return None

    try:
        # Load Raw
        df_m = load_csv("raw_data.zip")   # Market
        df_s = load_csv("specs_data.zip") # Specs
        df_p = load_csv("prices_data.zip") # Prices

        if df_m is None or df_s is None or df_p is None:
            raise ValueError("Zip files empty or missing.")

        # --- A. PREPARE MARKET (Standardize) ---
        df_m['join_make'] = df_m['Make'].astype(str).str.lower().str.strip()
        df_m['join_model'] = df_m['Model'].astype(str).str.lower().str.strip()

        # --- B. PREPARE SPECS (Standardize) ---
        # Specs has 'brand', 'model'
        s_make = next(c for c in df_s.columns if c.lower() in ['brand', 'make'])
        s_model = next(c for c in df_s.columns if c.lower() in ['model', 'model_name'])
        df_s['join_make'] = df_s[s_make].astype(str).str.lower().str.strip()
        df_s['join_model'] = df_s[s_model].astype(str).str.lower().str.strip()

        # --- C. PREPARE PRICES (Clean & Create Lookup) ---
        # Prices has 'Car_name' and 'Price.DE.'
        
        # 1. Clean Price Column (German format 46.220 -> 46220)
        p_price_col = next((c for c in df_p.columns if 'price' in c.lower()), None)
        if p_price_col:
            if df_p[p_price_col].dtype == object:
                # Remove dots used as thousand separators
                df_p[p_price_col] = df_p[p_price_col].astype(str).str.replace('.', '', regex=False)
            # Convert to Float and USD (approx 1.1x)
            df_p['Clean_Price'] = pd.to_numeric(df_p[p_price_col], errors='coerce') * 1.09
        
        # 2. Create "Full Name" key for matching
        if 'Car_name' in df_p.columns:
            df_p['full_name_match'] = df_p['Car_name'].astype(str).str.lower().str.strip()
        else:
            # Fallback if column names change
            p_make = next(c for c in df_p.columns if c.lower() in ['brand', 'make'])
            p_model = next(c for c in df_p.columns if c.lower() in ['model', 'model_name'])
            df_p['full_name_match'] = (df_p[p_make] + " " + df_p[p_model]).astype(str).str.lower().str.strip()

        # --- MERGE 1: MARKET + SPECS (Exact Match) ---
        # This gives us cars that exist in Real World AND have Engineering Specs
        df_range_merge = pd.merge(df_m, df_s, on=['join_make', 'join_model'], how='inner')
        
        # Add Range Logic (KM -> Miles)
        range_col = next((c for c in df_s.columns if 'range' in c.lower()), None)
        if range_col:
            df_range_merge['Final_Range_Miles'] = df_range_merge[range_col] * 0.621371
            df_range_merge = df_range_merge[df_range_merge['Final_Range_Miles'] > 10]

        # --- MERGE 2: SMART PRICE MATCH (The Fix) ---
        # Problem: Market has "model 3", Prices has "tesla model 3 long range"
        # Solution: Check if "tesla model 3" is INSIDE the price name.
        
        # Create dictionary: { "tesla model 3 long range...": 46220, ... }
        price_lookup = df_p.set_index('full_name_match')['Clean_Price'].to_dict()
        
        # Function to find price
        def find_smart_price(row):
            # Target: "tesla model 3"
            target = f"{row['join_make']} {row['join_model']}"
            
            # 1. Exact Match check
            if target in price_lookup:
                return price_lookup[target]
            
            # 2. Substring Match check (Is "tesla model 3" inside "tesla model 3 long range"?)
            # We iterate through price keys. If target is inside key, we take it.
            for key, price in price_lookup.items():
                if target in key: 
                    return price
            return np.nan

        # Apply to unique cars only (for speed)
        unique_models = df_range_merge[['join_make', 'join_model']].drop_duplicates()
        unique_models['Found_Price'] = unique_models.apply(find_smart_price, axis=1)
        
        # Merge prices back to the main 150k dataset
        df_final = pd.merge(df_range_merge, unique_models, on=['join_make', 'join_model'], how='left')
        
        # Filter for rows that actually found a price
        df_final['Final_Price_USD'] = df_final['Found_Price']
        df_final_strict = df_final.dropna(subset=['Final_Price_USD'])

        return df_final_strict, df_s, df_m, df_range_merge

    except Exception as e:
        st.error(f"Data Processing Error: {e}")
        return None, None, None, None

# --- EXECUTION ---
if 'df_main' not in st.session_state:
    if download_datasets():
        with st.spinner("Running Smart-Match Algorithm..."):
            df_final, df_specs, df_market_raw, df_range_merge = load_and_process_data()
            if df_final is not None:
                st.session_state['df_main'] = df_final         # A+B+C (Strict Price Match)
                st.session_state['df_specs'] = df_specs        # B (Specs Columns)
                st.session_state['df_market_raw'] = df_market_raw # A (Raw Market)
                st.session_state['df_range_merge'] = df_range_merge # A+B (Range Match)
                st.rerun()

# --- METRICS ---
if 'df_main' in st.session_state:
    df = st.session_state['df_main']
    st.markdown("---")
    
    # Check if we improved from 800 rows
    count = len(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Verified Vehicles", f"{count:,}")
    c2.metric("Avg Range", f"{df['Final_Range_Miles'].mean():.0f} mi")
    c3.metric("Avg Price", f"${df['Final_Price_USD'].mean():,.0f}")
    
    if count < 1000:
        st.warning(f"Match count low ({count}). This usually means the 'Smart Match' is too strict or names vary widely.")
    else:
        st.success(f"✅ Success! Matched {count:,} vehicles across all 3 datasets.")
