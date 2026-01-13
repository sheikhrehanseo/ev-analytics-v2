import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

st.set_page_config(page_title="Model Training", page_icon="🧪", layout="wide")

if 'df_main' not in st.session_state:
    st.warning("⚠️ Data not loaded. Please go to the Home page first.")
    st.stop()

df = st.session_state['df_main']

st.title("🧪 Model Training Lab")
st.markdown("### Training the AI on Physics + Economics")

# --- 1. AUTOMATIC FEATURE ENGINEERING ---
# We hardcode the features that actually matter (Engineering Decision)
FEATURES = [
    'battery_capacity_kWh', 
    'top_speed_kmh', 
    'acceleration_0_100_s', 
    'Final_Price_USD'
]
TARGET = 'Final_Range_Miles'

# Validate that these columns exist
available_features = [f for f in FEATURES if f in df.columns]
if len(available_features) < len(FEATURES):
    st.warning(f"⚠️ Some features are missing from the dataset. Using: {available_features}")

# --- 2. DATA SANITIZATION (The "Zero Score" Fix) ---
# Ensure all data is numeric. If it's text (like "4.5 sec"), force it to number.
model_df = df[available_features + [TARGET]].copy()
for col in model_df.columns:
    model_df[col] = pd.to_numeric(model_df[col], errors='coerce')

# Drop any rows that still have empty values (NaN)
model_df = model_df.dropna()

st.info(f"🧠 Training Model on **{len(model_df)}** verified vehicles using features: {available_features}")

# --- 3. TRAINING UI ---
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Hyperparameters")
    # Locked to Random Forest as requested
    st.success("Algorithm: **Random Forest Regressor**")
    
    split = st.slider("Train/Test Split", 0.1, 0.4, 0.2, help="How much data to keep for testing?")
    n_trees = st.slider("Number of Trees", 50, 500, 200, help="More trees = more accurate, but slower.")
    
    train_btn = st.button("🚀 Train Model", type="primary")

with c2:
    if train_btn:
        if len(model_df) > 50:
            with st.spinner("Training Random Forest..."):
                # Split Data
                X = model_df[available_features]
                y = model_df[TARGET]
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=split, random_state=42)
                
                # Init & Fit
                model = RandomForestRegressor(n_estimators=n_trees, random_state=42)
                model.fit(X_train, y_train)
                
                # Predict
                preds = model.predict(X_test)
                
                # Calculate Scores
                r2 = r2_score(y_test, preds)
                mae = mean_absolute_error(y_test, preds)
                mse = mean_squared_error(y_test, preds)
                rmse = np.sqrt(mse)
                
                # SAVE MODEL GLOBALLY
                st.session_state['active_model'] = {
                    'model': model,
                    'features': available_features,
                    'algo': "Random Forest"
                }
                
                # --- RESULTS DISPLAY ---
                st.success("✅ Training Complete!")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("R² Score (Accuracy)", f"{r2:.1%}", help="Closer to 100% is better")
                m2.metric("MAE (Error)", f"{mae:.1f} mi", help="Average error in miles")
                m3.metric("RMSE", f"{rmse:.1f}", help="Root Mean Squared Error")
                m4.metric("MSE", f"{mse:.1f}")
                
                # Feature Importance Chart
                st.subheader("What drives Range?")
                imp_df = pd.DataFrame({
                    'Feature': available_features,
                    'Importance': model.feature_importances_
                }).sort_values('Importance', ascending=True)
                
                fig = px.bar(imp_df, x='Importance', y='Feature', orientation='h', 
                             title="Feature Importance (Impact on Range)",
                             color='Importance', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
                
                # Prediction vs Actual Chart
                fig_scat = px.scatter(x=y_test, y=preds, labels={'x': 'Actual Range', 'y': 'Predicted Range'},
                                      title="Accuracy: Actual vs Predicted")
                fig_scat.add_shape(type="line", x0=y.min(), y0=y.min(), x1=y.max(), y1=y.max(), 
                                   line=dict(color="Red", dash="dash"))
                st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.error(f"⚠️ Not enough data points ({len(model_df)}) to train a reliable model. We need at least 50.")
