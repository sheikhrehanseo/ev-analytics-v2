import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

st.set_page_config(page_title="Model Lab", page_icon="🧪", layout="wide")

if 'df_main' not in st.session_state:
    st.warning("⚠️ Data not loaded. Please go to the Home page first.")
    st.stop()

df = st.session_state['df_main']
st.title("🧪 Model Training Lab")

# Detect Physics Columns
all_num = df.select_dtypes(include=np.number).columns.tolist()
batt_col = next((c for c in all_num if 'batt' in c.lower() and 'cap' in c.lower()), None)
speed_col = next((c for c in all_num if 'speed' in c.lower()), None)
eff_col = next((c for c in all_num if 'effic' in c.lower()), None)
accel_col = next((c for c in all_num if 'accel' in c.lower()), None)

col_conf, col_run = st.columns([1, 2])

with col_conf:
    st.subheader("Configuration")
    algo = st.selectbox("Algorithm", ["Random Forest", "Gradient Boosting"])
    split = st.slider("Train/Test Split", 0.1, 0.4, 0.2)
    n_trees = st.slider("Number of Trees", 50, 500, 100)
    
    st.markdown("**Features (X):**")
    default_feats = [f for f in [batt_col, 'Final_Price_USD', speed_col] if f]
    possible = [f for f in [batt_col, speed_col, eff_col, accel_col, 'Final_Price_USD'] if f]
    features = st.multiselect("Select Inputs", possible, default=default_feats)
    
    train = st.button("🚀 Train Model", type="primary")

with col_run:
    if train:
        if features:
            with st.spinner(f"Training {algo}..."):
                X = df[features].dropna()
                y = df.loc[X.index, 'Final_Range_Miles']
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=split, random_state=42)
                
                if algo == "Random Forest":
                    model = RandomForestRegressor(n_estimators=n_trees, random_state=42)
                else:
                    model = GradientBoostingRegressor(n_estimators=n_trees, random_state=42)
                
                model.fit(X_train, y_train)
                preds = model.predict(X_test)
                
                # Metrics
                r2 = r2_score(y_test, preds)
                mae = mean_absolute_error(y_test, preds)
                mse = mean_squared_error(y_test, preds)
                rmse = np.sqrt(mse)
                
                st.success(f"Training Complete!")
                
                # Metric Cards
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("R² Score", f"{r2:.2%}")
                m2.metric("MAE", f"{mae:.2f} mi")
                m3.metric("RMSE", f"{rmse:.2f}")
                m4.metric("MSE", f"{mse:.2f}")
                
                # Plot
                fig = px.scatter(x=y_test, y=preds, labels={'x': 'Actual', 'y': 'Predicted'}, 
                                 title="Prediction Accuracy")
                fig.add_shape(type="line", x0=y.min(), y0=y.min(), x1=y.max(), y1=y.max(), 
                              line=dict(color="Red", dash="dash"))
                st.plotly_chart(fig, use_container_width=True)
                
                # Save
                st.session_state['active_model'] = {'model': model, 'features': features, 'algo': algo}
        else:
            st.error("Select at least 1 feature.")
