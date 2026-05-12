import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(page_title="BDO Barter Stock Tracker", layout="wide")

st.title("🏴‍☠️ Black Desert Online - Bartering Dashboard")
st.markdown("Track your sea trade goods, check low-stock items, and analyze inventory levels.")

# --- DATA INGESTION ---
# For demonstration purposes, we're creating a mock DataFrame.
# You can replace this logic by loading your sheet using gspread or reading a CSV export.
@st.cache_data
def load_data():
    # Example structure matching the "Full Barter Stock" structure
    data = {
        "Item Name": [
            "Level 1 Fertile Soil", "Level 1 Unidentified Ancient Mural", 
            "Level 2 Monster Tentacle", "Level 2 Filtered Drinking Water",
            "Level 3 Ancient Orders", "Level 3 Lopters Fishnet",
            "Level 4 Green Salt Lump", "Level 4 Panacea",
            "Level 5 Statue's Tear", "Level 5 Mysterious Rock",
            "Level 1 Stained Seagull Figurine", "Level 5 102 Year Old Golden Herb"
        ],
        "Level": [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 1, 5],
        "Quantity": [12, 3, 5, 2, 8, 1, 14, 4, 0, 7, 2, 6]
    }
    return pd.DataFrame(data)

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Navigation & Filters")
selected_level = st.sidebar.multiselect(
    "Filter by Item Level",
    options=[1, 2, 3, 4, 5],
    default=[1, 2, 3, 4, 5]
)

# Apply filter
filtered_df = df[df["Level"].isin(selected_level)]

# --- METRICS / KPIS ---
st.markdown("### 📊 Quick Status")
col1, col2, col3 = st.columns(3)

total_items = len(filtered_df)
low_stock = len(filtered_df[filtered_df["Quantity"] < 5])
out_of_stock = len(filtered_df[filtered_df["Quantity"] == 0])

col1.metric("Total Items Monitored", total_items)
col2.metric("Items Below Par (< 5)", low_stock, delta=-1, delta_color="inverse")
col3.metric("Out of Stock", out_of_stock, delta_color="inverse")

st.markdown("---")

# --- CENTRAL AREA: TWO COLUMNS ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 🚨 Items to Restock (Quantity < 5)")
    needs_restock = filtered_df[filtered_df["Quantity"] < 5].sort_values(by="Quantity")
    
    # Display as a styled data frame
    st.dataframe(
        needs_restock, 
        column_config={
            "Item Name": "Item",
            "Level": "Tier",
            "Quantity": "Stock"
        },
        use_container_width=True
    )

with col_right:
    st.markdown("### 🔍 Search Inventory")
    search_term = st.text_input("Enter item name to check:")
    
    if search_term:
        search_results = filtered_df[filtered_df["Item Name"].str.contains(search_term, case=False, na=False)]
        st.dataframe(search_results, use_container_width=True)
    else:
        st.info("Type above to search across your tiers...")

st.markdown("---")

# --- VISUALIZATION / GRAPHS ---
st.markdown("### 📈 Inventory Quantities by Level")

# Group data by level to show totals
level_summary = filtered_df.groupby("Level")["Quantity"].sum().reset_index()

st.bar_chart(
    level_summary, 
    x="Level", 
    y="Quantity", 
    color="Level",
    use_container_width=True
)