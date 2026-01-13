import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

if 'df_market_raw' not in st.session_state:
    st.warning("⚠️ Data not loaded. Please go to the Home page first.")
    st.stop()

# DATA SOURCES
df_raw = st.session_state['df_market_raw']      # 150k+ rows (Use for Growth/Share)
df_price_match = st.session_state['df_main']    # Strict match (Use for Price Charts)
df_range_match = st.session_state['df_range_merge'] # A+B match (Use for Range Charts)

st.title("📈 Market Intelligence Dashboard")
st.markdown("### Comprehensive analysis of EV adoption trends and manufacturer dominance.")
st.markdown("---")

# --- 1. MARKET ADOPTION TREND ---
st.subheader("1. EV Market Growth Trend")
counts = df_raw['Model Year'].value_counts().reset_index()
counts.columns = ['Year', 'Sales']
counts = counts.sort_values('Year')
counts = counts[counts['Year'] > 2010]
fig_growth = px.area(counts, x='Year', y='Sales', markers=True, color_discrete_sequence=['#00FF99'])
st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")

# --- 2. MANUFACTURER MARKET SHARE ---
st.subheader("2. Manufacturer Market Share")
c1, c2 = st.columns([2, 1])
with c1:
    share_counts = df_raw['Make'].value_counts().nlargest(10).reset_index()
    share_counts.columns = ['Make', 'Count']
    fig_share = px.pie(share_counts, values='Count', names='Make', hole=0.4, 
                 color_discrete_sequence=px.colors.sequential.Viridis,
                 title="Top 10 Brands by Volume")
    st.plotly_chart(fig_share, use_container_width=True)
with c2:
    st.markdown("**Insight:**")
    top_brand = share_counts.iloc[0]['Make']
    top_val = share_counts.iloc[0]['Count']
    st.info(f"The market is currently dominated by **{top_brand}** with {top_val:,} registered vehicles.")

st.markdown("---")

# --- 3. GEOGRAPHIC HOTSPOTS ---
st.subheader("3. Geographic Hotspots")
geo_view = st.radio("Group By:", ["County", "City"], horizontal=True)
geo_counts = df_raw[geo_view].value_counts().nlargest(10).reset_index()
geo_counts.columns = [geo_view, 'Count']
fig_geo = px.bar(geo_counts, x=geo_view, y='Count', color='Count',
             color_continuous_scale='Bluered', title=f"Top 10 {geo_view}s for EV Adoption")
st.plotly_chart(fig_geo, use_container_width=True)

st.markdown("---")

# --- 4. TECHNICAL LEADERBOARDS ---
st.subheader("4. Technical Leaderboards")

# Metric Selector
metric = st.radio("Rank By:", ["Range (Miles)", "Price (Highest)", "Price (Lowest)"], horizontal=True)

if metric == "Range (Miles)":
    # USE A+B DATASET (Much larger match rate)
    st.caption(f"Showing top range models from {len(df_range_match)} spec-verified vehicles.")
    top10 = df_range_match[['Make', 'Model', 'Final_Range_Miles']].drop_duplicates().nlargest(10, 'Final_Range_Miles')
    fig_lead = px.bar(top10, x='Final_Range_Miles', y='Model', color='Make', orientation='h', title="Longest Range EVs")
    st.plotly_chart(fig_lead, use_container_width=True)

elif "Price" in metric:
    # USE A+B+C DATASET (Strict match required for price)
    st.caption(f"Showing verified pricing for {len(df_price_match)} models.")
    if len(df_price_match) > 0:
        if "Highest" in metric:
            top10 = df_price_match[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nlargest(10, 'Final_Price_USD')
            title_text = "Most Expensive EVs"
        else:
            top10 = df_price_match[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nsmallest(10, 'Final_Price_USD')
            title_text = "Most Affordable EVs"
            
        fig_lead = px.bar(top10, x='Final_Price_USD', y='Model', color='Make', orientation='h', title=title_text)
        st.plotly_chart(fig_lead, use_container_width=True)
    else:
        st.warning("Not enough price data matched to generate this chart.")
