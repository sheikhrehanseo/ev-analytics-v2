import streamlit as st
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

st.set_page_config(page_title="Model Training Lab", page_icon="🧪", layout="wide")

@st.cache_data
def load_data():
    prices = pd.read_csv('prices_data.zip')
    # Renaming for consistency
    prices = prices.rename(columns={
        'acceleration..0.100.': 'acceleration_0_100',
        'Price.DE.': 'price_de',
        'Top_speed': 'top_speed',
        'Fast_charge': 'fast_charge'
    })
    return prices

prices_df = load_data()

st.title("🧪 Model Training Lab")
st.markdown("Train machine learning models to predict EV Range & Price")

# Data Preparation
df = prices_df.copy()
# Drop rows where Targets are missing
df = df.dropna(subset=['Range', 'price_de'])
df = df[df['price_de'] > 0]

# Feature Selection
features = ['Battery', 'Efficiency', 'top_speed', 'acceleration_0_100', 'fast_charge']

# Sidebar
st.sidebar.header("Model Configuration")
prediction_target = st.sidebar.selectbox("Prediction Target", ["Range (km)", "Price (€)", "Both"])
model_choice = st.sidebar.selectbox("Select Model", ["Random Forest Regressor", "Gradient Boosting Regressor"])
test_size = st.sidebar.slider("Test Size (%)", 10, 40, 20) / 100
random_state = st.sidebar.number_input("Random State", 0, 100, 42)

if st.sidebar.button("Train Model", type="primary"):
    with st.spinner("Training model(s)..."):
        
        # 1. Split Data FIRST (Fixes Data Leakage)
        X = df[features]
        # We need to split X first to calculate median on Train set only
        X_train_raw, X_test_raw, indices_train, indices_test = train_test_split(
            X, X.index, test_size=test_size, random_state=random_state
        )
        
        # 2. Impute Missing Values (Calculate median on TRAIN, apply to BOTH)
        train_medians = X_train_raw.median()
        X_train = X_train_raw.fillna(train_medians)
        X_test = X_test_raw.fillna(train_medians)
        
        # Save medians for the Prediction Page (Crucial for Pipeline consistency)
        with open('model_medians.pkl', 'wb') as f:
            pickle.dump(train_medians.to_dict(), f)
        
        def train_and_evaluate(y_data, target_name):
            # Split target using same indices
            y_train = y_data.loc[indices_train]
            y_test = y_data.loc[indices_test]
            
            if model_choice == "Random Forest Regressor":
                model = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)
            else:
                model = GradientBoostingRegressor(n_estimators=100, random_state=random_state)
            
            model.fit(X_train, y_train)
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            metrics = {
                'r2_test': r2_score(y_test, y_pred_test),
                'r2_train': r2_score(y_train, y_pred_train),
                'rmse_test': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'rmse_train': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'mae_test': mean_absolute_error(y_test, y_pred_test),
                'mae_train': mean_absolute_error(y_train, y_pred_train)
            }
            return model, metrics

        # Training Execution
        if prediction_target == "Range (km)" or prediction_target == "Both":
            model_range, m_range = train_and_evaluate(df['Range'], "Range")
            
            # Save Model
            with open('model_range.pkl', 'wb') as f:
                pickle.dump(model_range, f)
                
            st.success(f"✅ {model_choice} for Range trained!")
            col1, col2, col3 = st.columns(3)
            col1.metric("R² Score (Test)", f"{m_range['r2_test']:.4f}")
            col2.metric("RMSE (Test)", f"{m_range['rmse_test']:.2f} km")
            col3.metric("MAE (Test)", f"{m_range['mae_test']:.2f} km")

        if prediction_target == "Price (€)" or prediction_target == "Both":
            model_price, m_price = train_and_evaluate(df['price_de'], "Price")
            
            # Save Model
            with open('model_price.pkl', 'wb') as f:
                pickle.dump(model_price, f)

            st.success(f"✅ {model_choice} for Price trained!")
            col1, col2, col3 = st.columns(3)
            col1.metric("R² Score (Test)", f"{m_price['r2_test']:.4f}")
            col2.metric("RMSE (Test)", f"{m_price['rmse_test']:.2f} €")
            col3.metric("MAE (Test)", f"{m_price['mae_test']:.2f} €")

        st.success("💾 Models and Imputation Medians saved successfully!")

else:
    st.info("👈 Configure and click 'Train Model' to begin")
    st.subheader("📋 Training Data Preview (Pre-Split)")
    st.dataframe(df[features + ['Range', 'price_de']].head(), use_container_width=True)
