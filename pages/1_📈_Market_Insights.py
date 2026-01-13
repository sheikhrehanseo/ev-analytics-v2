import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Market Insights", page_icon="📈", layout="wide")

if 'df_market_raw' not in st.session_state:
    st.warning("⚠️ Data not loaded. Please go to the Home page first.")
    st.stop()

# USE THE RAW DATA (150k+ rows) for Market Charts
df_raw = st.session_state['df_market_raw']
# USE THE MERGED DATA (Strict rows) for Leaderboards
df_merged = st.session_state['df_main']

st.title("📈 Market Intelligence Dashboard")
st.markdown("### Comprehensive analysis of EV adoption trends and manufacturer dominance.")

st.markdown("---")

# --- 1. MARKET ADOPTION TREND ---
st.subheader("1. EV Market Growth Trend")
counts = df_raw['Model Year'].value_counts().reset_index()
counts.columns = ['Year', 'Sales']
counts = counts.sort_values('Year')
# Filter out future years or bad data if needed
counts = counts[counts['Year'] > 2010]
fig_growth = px.area(counts, x='Year', y='Sales', markers=True, 
              color_discrete_sequence=['#00FF99'])
st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")

# --- 2. MANUFACTURER MARKET SHARE ---
st.subheader("2. Manufacturer Market Share")
c1, c2 = st.columns([2, 1])

with c1:
    # Top 10 Manufacturers
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

# --- 4. PERFORMANCE LEADERBOARDS (Requires Merged Data) ---
st.subheader("4. Technical Leaderboards (Verified Models Only)")
st.caption(f"Showing specs for {len(df_merged)} fully verified models (Market + Specs + Price match).")

if len(df_merged) > 0:
    metric = st.radio("Rank By:", ["Range (Miles)", "Price (Highest)", "Price (Lowest)"], horizontal=True)
    
    if metric == "Range (Miles)":
        top10 = df_merged[['Make', 'Model', 'Final_Range_Miles']].drop_duplicates().nlargest(10, 'Final_Range_Miles')
        fig_lead = px.bar(top10, x='Final_Range_Miles', y='Model', color='Make', orientation='h', title="Longest Range EVs")
    elif metric == "Price (Highest)":
        top10 = df_merged[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nlargest(10, 'Final_Price_USD')
        fig_lead = px.bar(top10, x='Final_Price_USD', y='Model', color='Make', orientation='h', title="Most Expensive EVs")
    else:
        top10 = df_merged[['Make', 'Model', 'Final_Price_USD']].drop_duplicates().nsmallest(10, 'Final_Price_USD')
        fig_lead = px.bar(top10, x='Final_Price_USD', y='Model', color='Make', orientation='h', title="Most Affordable EVs")
    
    st.plotly_chart(fig_lead, use_container_width=True)
else:
    st.warning("Not enough matches between datasets to show Leaderboards.")
