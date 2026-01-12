import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

if 'df_main' not in st.session_state:
    st.warning("⚠️ Data not loaded. Please go to the Home page first.")
    st.stop()

df = st.session_state['df_main']

st.title("📈 Market Intelligence Dashboard")

# --- CONTROL PANEL ---
analysis_type = st.selectbox("Select Analysis Module:", 
                             ["EV Market Growth", "Manufacturer Share", 
                              "Top 10 Leaderboards", "Geographic Hotspots", 
                              "Car vs Car Comparison"])
st.markdown("---")

# --- VISUALIZATIONS ---
if analysis_type == "EV Market Growth":
    counts = df['Model Year'].value_counts().reset_index()
    counts.columns = ['Year', 'Sales']
    counts = counts.sort_values('Year')
    fig = px.area(counts, x='Year', y='Sales', title="EV Adoption Trend", 
                  color_discrete_sequence=['#00FF99'])
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Manufacturer Share":
    counts = df['Make'].value_counts().reset_index()
    counts.columns = ['Make', 'Count']
    fig = px.pie(counts, values='Count', names='Make', title="Market Share by Brand", 
                 hole=0.4, color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Top 10 Leaderboards":
    metric = st.radio("Rank By:", ["Range (Miles)", "Price (Highest)", "Price (Lowest)"])
    
    if metric == "Range (Miles)":
        top10 = df[['Make', 'Model', 'Final_Range_Miles']].drop_duplicates().nlargest(10, 'Final_Range_Miles')
        fig = px.bar(top10, x='Final_Range_Miles', y='Model', color='Make', orientation='h', title="Longest Range EVs")
    elif metric == "Price (Highest)":
        top10 = df[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nlargest(10, 'Final_Price_USD')
        fig = px.bar(top10, x='Final_Price_USD', y='Model', color='Make', orientation='h', title="Most Expensive EVs")
    else:
        top10 = df[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nsmallest(10, 'Final_Price_USD')
        fig = px.bar(top10, x='Final_Price_USD', y='Model', color='Make', orientation='h', title="Most Affordable EVs")
    
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Geographic Hotspots":
    geo_view = st.radio("Group By:", ["County", "City"])
    geo_counts = df[geo_view].value_counts().nlargest(10).reset_index()
    geo_counts.columns = [geo_view, 'Count']
    fig = px.bar(geo_counts, x=geo_view, y='Count', title=f"Top 10 {geo_view}s", color='Count')
    st.plotly_chart(fig, use_container_width=True)

elif analysis_type == "Car vs Car Comparison":
    c1, c2 = st.columns(2)
    cars = sorted(df['Model'].unique())
    with c1:
        car_a = st.selectbox("Select Car A", cars, index=0)
    with c2:
        car_b = st.selectbox("Select Car B", cars, index=1)
    
    data_a = df[df['Model'] == car_a].iloc[0]
    data_b = df[df['Model'] == car_b].iloc[0]
    
    fig = go.Figure(data=[
        go.Bar(name=car_a, x=['Range', 'Price'], y=[data_a['Final_Range_Miles'], data_a['Final_Price_USD']]),
        go.Bar(name=car_b, x=['Range', 'Price'], y=[data_b['Final_Range_Miles'], data_b['Final_Price_USD']])
    ])
    fig.update_layout(barmode='group', title="Direct Comparison")
    st.plotly_chart(fig, use_container_width=True)
