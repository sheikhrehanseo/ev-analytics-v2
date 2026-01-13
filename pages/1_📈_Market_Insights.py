import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

@st.cache_data
def load_data():
    # Only load what is used
    prices = pd.read_csv('prices_data.zip')
    raw = pd.read_csv('raw_data.zip')
    
    # Rename columns to standard snake_case to avoid naming issues
    prices = prices.rename(columns={
        'acceleration..0.100.': 'acceleration_0_100',
        'Price.DE.': 'price_de',
        'Top_speed': 'top_speed',
        'Fast_charge': 'fast_charge'
    })
    return prices, raw

try:
    prices_df, raw_df = load_data()
except FileNotFoundError:
    st.error("❌ CSV files not found. Please ensure 'prices_data.csv' and 'raw_data.csv' are in the directory.")
    st.stop()

st.title("📈 EV Market Insights Dashboard")

# Sidebar filters
st.sidebar.header("🔧 Filters")
price_sort = st.sidebar.selectbox("Price Sorting", ["Highest", "Lowest"])
speed_sort = st.sidebar.selectbox("Speed Sorting", ["Highest", "Lowest"])
range_sort = st.sidebar.selectbox("Range Sorting", ["Highest", "Lowest"])
location_type = st.sidebar.selectbox("Location Analysis", ["County", "City", "State"])

# Row 1: Market Overview
st.header("📊 Market Overview")
col1, col2 = st.columns(2)

with col1:
    if 'Model Year' in raw_df.columns:
        growth = raw_df['Model Year'].value_counts().sort_index()
        fig = px.line(x=growth.index, y=growth.values, labels={'x': 'Year', 'y': 'Number of EVs'},
                      title="EV Market Growth Trend")
        fig.update_traces(line_color='#00CC96', line_width=3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Model Year data not available.")

with col2:
    if 'Make' in raw_df.columns:
        market_share = raw_df['Make'].value_counts().head(10)
        fig = px.pie(values=market_share.values, names=market_share.index, 
                     title="Top 10 Manufacturers Market Share")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Manufacturer data not available.")

# Row 2: Top 10 Cars Performance
st.header("🏆 Top 10 Cars Performance")
col1, col2, col3 = st.columns(3)

# Filter out zero/missing prices for the ranking
prices_clean = prices_df[prices_df['price_de'] > 0]

with col1:
    if price_sort == "Highest":
        top_price = prices_clean.nlargest(10, 'price_de')[['Car_name', 'price_de']]
        title = "Top 10 Most Expensive EVs"
    else:
        top_price = prices_clean.nsmallest(10, 'price_de')[['Car_name', 'price_de']]
        title = "Top 10 Most Affordable EVs"
    fig = px.bar(top_price, x='price_de', y='Car_name', orientation='h',
                 title=title, labels={'price_de': 'Price (€)'}, color='price_de')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if speed_sort == "Highest":
        top_speed = prices_df.nlargest(10, 'top_speed')[['Car_name', 'top_speed']]
        title = "Top 10 Fastest EVs"
    else:
        top_speed = prices_df.nsmallest(10, 'top_speed')[['Car_name', 'top_speed']]
        title = "Top 10 Slowest EVs"
    fig = px.bar(top_speed, x='top_speed', y='Car_name', orientation='h',
                 title=title, labels={'top_speed': 'Top Speed (km/h)'}, color='top_speed')
    st.plotly_chart(fig, use_container_width=True)

with col3:
    if range_sort == "Highest":
        top_range = prices_df.nlargest(10, 'Range')[['Car_name', 'Range']]
        title = "Top 10 Longest Range EVs"
    else:
        top_range = prices_df.nsmallest(10, 'Range')[['Car_name', 'Range']]
        title = "Top 10 Shortest Range EVs"
    fig = px.bar(top_range, x='Range', y='Car_name', orientation='h',
                 title=title, labels={'Range': 'Range (km)'}, color='Range')
    st.plotly_chart(fig, use_container_width=True)

# Row 3: Geographic Distribution
st.header("🗺️ Geographic Distribution")
# (Kept mostly same, assuming raw_data columns exist)
if location_type == "County" and 'County' in raw_df.columns:
    top_locations = raw_df['County'].value_counts().head(10).index
    filtered = raw_df[raw_df['County'].isin(top_locations)]
    make_location = filtered.groupby(['County', 'Make']).size().reset_index(name='Count')
    top_makes = raw_df['Make'].value_counts().head(10).index
    make_location = make_location[make_location['Make'].isin(top_makes)]
    fig = px.bar(make_location, x='County', y='Count', color='Make',
                 title="Top 10 Makes Distribution Across Top 10 Counties")
    st.plotly_chart(fig, use_container_width=True)

elif location_type == "City" and 'City' in raw_df.columns:
    top_locations = raw_df['City'].value_counts().head(10).index
    filtered = raw_df[raw_df['City'].isin(top_locations)]
    make_location = filtered.groupby(['City', 'Make']).size().reset_index(name='Count')
    top_makes = raw_df['Make'].value_counts().head(10).index
    make_location = make_location[make_location['Make'].isin(top_makes)]
    fig = px.bar(make_location, x='City', y='Count', color='Make',
                 title="Top 10 Makes Distribution Across Top 10 Cities")
    st.plotly_chart(fig, use_container_width=True)
    
elif 'State' in raw_df.columns:
    make_location = raw_df.groupby(['State', 'Make']).size().reset_index(name='Count')
    top_makes = raw_df['Make'].value_counts().head(10).index
    make_location = make_location[make_location['Make'].isin(top_makes)]
    fig = px.bar(make_location, x='State', y='Count', color='Make',
                 title="Top 10 Makes Distribution by State")
    st.plotly_chart(fig, use_container_width=True)

# Row 4: Car Comparison
st.header("🔄 Compare Two Cars")
col1, col2 = st.columns(2)
car_list = prices_df['Car_name'].unique()
with col1:
    car1 = st.selectbox("Select First Car", car_list, key='car1')
with col2:
    car2 = st.selectbox("Select Second Car", car_list, key='car2')

if car1 and car2:
    car1_data = prices_df[prices_df['Car_name'] == car1].iloc[0]
    car2_data = prices_df[prices_df['Car_name'] == car2].iloc[0]
    
    # Updated column names here
    metrics = ['Battery', 'Range', 'top_speed', 'price_de', 'Efficiency', 'fast_charge', 'acceleration_0_100']
    
    # Handle NaNs for the plot to avoid errors
    c1_vals = [car1_data[m] if pd.notna(car1_data[m]) else 0 for m in metrics]
    c2_vals = [car2_data[m] if pd.notna(car2_data[m]) else 0 for m in metrics]

    comparison = pd.DataFrame({
        car1: c1_vals,
        car2: c2_vals
    }, index=['Battery (kWh)', 'Range (km)', 'Top Speed (km/h)', 'Price (€)', 
              'Efficiency (Wh/km)', 'Fast Charge (kW)', 'Acceleration 0-100 (s)'])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name=car1, x=comparison.index, y=comparison[car1]))
    fig.add_trace(go.Bar(name=car2, x=comparison.index, y=comparison[car2]))
    fig.update_layout(title="Car Comparison", barmode='group', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(comparison, use_container_width=True)
