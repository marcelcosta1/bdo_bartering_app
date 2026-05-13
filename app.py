import streamlit as st
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(page_title="BDO Barter Stock Tracker", layout="wide")

st.title("🏴‍☠️ Black Desert Online - Bartering Dashboard")
st.markdown("Track your sea trade goods, check low-stock items, and analyze inventory levels.")

# --- DATA INGESTION ---
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        # Optionally, rename columns if needed to match expected names
        # df = df.rename(columns={"YourColumn1": "Item Name", ...})
        return df
    else:
        return pd.DataFrame(columns=["Item Name", "Level", "Quantity"])

st.sidebar.header("Navigation & Filters")
uploaded_file = st.sidebar.file_uploader(
    "Upload your Barter Stock Excel file (.xlsx)", 
    type=["xlsx"]
)

df = load_data(uploaded_file)

if df.empty:
    st.warning("Please upload a valid Excel file with columns: Item Name, Level, Quantity.")
    st.stop()

# --- SIDEBAR FILTERS ---
selected_level = st.sidebar.multiselect(
    "Filter by Item Level",
    options=sorted(df["Level"].dropna().unique()),
    default=sorted(df["Level"].dropna().unique())
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

level_summary = filtered_df.groupby("Level")["Quantity"].sum().reset_index()

st.bar_chart(
    level_summary, 
    x="Level", 
    y="Quantity", 
    color="Level",
    use_container_width=True
)