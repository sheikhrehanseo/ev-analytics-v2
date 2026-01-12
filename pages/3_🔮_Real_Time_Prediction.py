import streamlit as st
import numpy as np

st.set_page_config(page_title="Predictor", page_icon="🔮", layout="wide")

if 'df_main' not in st.session_state:
    st.warning("⚠️ Data not loaded. Go to Home.")
    st.stop()

if 'active_model' not in st.session_state:
    st.warning("⚠️ No Model Trained. Go to 'Model Training' page first.")
    st.stop()

df = st.session_state['df_main']
model_pack = st.session_state['active_model']
model = model_pack['model']
feats = model_pack['features']

st.title("🔮 Real-Time Range Predictor")
st.info(f"Active Model: **{model_pack['algo']}**")

# --- UI ---
st.subheader("1. Auto-Fill (Select Base Car)")
car_pick = st.selectbox("Choose car template:", sorted(df['Model'].unique()))
car_data = df[df['Model'] == car_pick].iloc[0]

st.subheader("2. Modify Specs")
inputs = []
cols = st.columns(len(feats))

for i, f in enumerate(feats):
    # Default to selected car's value
    def_val = float(car_data[f]) if f in car_data else float(df[f].mean())
    val = cols[i].number_input(f"{f}", value=def_val)
    inputs.append(val)

st.markdown("---")
if st.button("✨ Predict Range", type="primary"):
    pred = model.predict([inputs])[0]
    
    c1, c2 = st.columns([1, 2])
    c1.metric("Predicted Range", f"{pred:.1f} Miles")
    
    orig = car_data['Final_Range_Miles']
    diff = pred - orig
    
    if diff > 0.5:
        c2.success(f"🚀 +{diff:.1f} miles vs {car_pick}")
    elif diff < -0.5:
        c2.error(f"📉 {diff:.1f} miles vs {car_pick}")
    else:
        c2.info(f"⚖️ Same as {car_pick}")
