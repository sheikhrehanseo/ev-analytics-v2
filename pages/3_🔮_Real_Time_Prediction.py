import streamlit as st
import pandas as pd
import pickle
import os
import math

st.set_page_config(page_title="Real-Time Prediction", page_icon="🔮", layout="wide")

@st.cache_data
def load_data():
    prices = pd.read_csv('prices_data.zip')
    prices = prices.rename(columns={
        'acceleration..0.100.': 'acceleration_0_100',
        'Price.DE.': 'price_de',
        'Top_speed': 'top_speed',
        'Fast_charge': 'fast_charge'
    })
    return prices

prices_df = load_data()

st.title("🔮 Real-Time EV Range & Price Prediction")
st.markdown("Predict the range and price of an electric vehicle based on its specifications")

# Check for Models
range_exists = os.path.exists('model_range.pkl')
price_exists = os.path.exists('model_price.pkl')
medians_exists = os.path.exists('model_medians.pkl')

if not (range_exists and price_exists and medians_exists):
    st.warning("⚠️ Trained models or medians not found!")
    st.info("Please go to the **Model Training Lab** to train and save the models first.")
    # This creates a direct link to the training page
    st.page_link("pages/2_🧪_Model_Training.py", label="Go to Model Training Lab", icon="🧪")
    st.stop()

# Load Models & Medians
with open('model_range.pkl', 'rb') as f:
    model_range = pickle.load(f)
with open('model_price.pkl', 'rb') as f:
    model_price = pickle.load(f)
with open('model_medians.pkl', 'rb') as f:
    medians = pickle.load(f)

# Helper for Safe Value Extraction (Prevents Crashes)
def get_safe_value(val, default_key):
    # If val is NaN or None, return the training median for that feature
    if pd.isna(val) or val is None:
        return float(medians.get(default_key, 0.0))
    return float(val)

# Prediction interface
st.subheader("🎯 Enter Vehicle Specifications")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Option 1: Select Existing Car")
    car_name = st.selectbox("Choose a car", ["Custom Input"] + list(prices_df['Car_name'].unique()))
    
    if car_name != "Custom Input":
        car_data = prices_df[prices_df['Car_name'] == car_name].iloc[0]
        # Use safe extraction
        battery = get_safe_value(car_data['Battery'], 'Battery')
        efficiency = get_safe_value(car_data['Efficiency'], 'Efficiency')
        top_speed = get_safe_value(car_data['top_speed'], 'top_speed')
        acceleration = get_safe_value(car_data['acceleration_0_100'], 'acceleration_0_100')
        fast_charge = get_safe_value(car_data['fast_charge'], 'fast_charge')
        actual_range = car_data['Range']
        actual_price = car_data['price_de']
    else:
        # Defaults if Custom Input
        battery = medians['Battery']
        efficiency = medians['Efficiency']
        top_speed = medians['top_speed']
        acceleration = medians['acceleration_0_100']
        fast_charge = medians['fast_charge']
        actual_range = None
        actual_price = None

with col2:
    st.markdown("#### Option 2: Custom Input")
    st.info("Adjust values below. Defaults are based on selection or training data medians.")

# Input fields (Updated constraints for modern EVs)
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    battery_input = st.number_input(
        "Battery Capacity (kWh)", 
        min_value=10.0, max_value=250.0, # Increased max for trucks
        value=battery, step=1.0
    )
    efficiency_input = st.number_input(
        "Efficiency (Wh/km)", 
        min_value=50.0, max_value=500.0, 
        value=efficiency, step=1.0
    )

with col2:
    top_speed_input = st.number_input(
        "Top Speed (km/h)", 
        min_value=80.0, max_value=450.0, # Increased max for hypercars
        value=top_speed, step=1.0
    )
    acceleration_input = st.number_input(
        "Acceleration 0-100 km/h (s)", 
        min_value=1.0, max_value=30.0, # Decreased min for plaid/nevera
        value=acceleration, step=0.1
    )

with col3:
    fast_charge_input = st.number_input(
        "Fast Charge Power (kW)", 
        min_value=0.0, max_value=1000.0, 
        value=fast_charge, step=1.0
    )

# Predict button
if st.button("🚀 Predict Range & Price", type="primary", use_container_width=True):
    # Prepare input (Must match training feature order and names)
    input_data = pd.DataFrame({
        'Battery': [battery_input],
        'Efficiency': [efficiency_input],
        'top_speed': [top_speed_input],
        'acceleration_0_100': [acceleration_input],
        'fast_charge': [fast_charge_input]
    })
    
    # Make predictions
    predicted_range = model_range.predict(input_data)[0]
    predicted_price = model_price.predict(input_data)[0]
    
    # Display results
    st.markdown("---")
    st.subheader("📊 Prediction Results")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔋 Predicted Range", f"{predicted_range:.1f} km")
    if actual_range and pd.notna(actual_range):
        c2.metric("📏 Actual Range", f"{actual_range:.1f} km", delta=f"{predicted_range - actual_range:.1f}")
    
    c3.metric("💰 Predicted Price", f"{predicted_price:,.0f} €")
    if actual_price and pd.notna(actual_price):
        c4.metric("💵 Actual Price", f"{actual_price:,.0f} €", delta=f"{predicted_price - actual_price:,.0f}")
    
    # Detailed breakdown
    st.markdown("---")
    st.subheader("⚡ Estimation Breakdown")
    
    col1, col2 = st.columns(2)
    with col1:
        # Physics calc check
        if efficiency_input > 0:
            theoretical = (battery_input * 1000) / efficiency_input
            st.info(f"**Physics-only Range (Battery/Eff)**: {theoretical:.1f} km")
        st.success(f"**AI Model Range**: {predicted_range:.1f} km")
        st.caption("The AI model adjusts for aerodynamics (top speed) and weight factors (implied by acceleration).")
