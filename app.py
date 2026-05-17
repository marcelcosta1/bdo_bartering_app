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
        # Ensure column types are clean to prevent search/filter errors
        if "Item Name" in df.columns:
            df["Item Name"] = df["Item Name"].astype(str).str.strip()
        return df
    else:
        return pd.DataFrame(columns=["Item Name", "Level", "Quantity"])

# --- SIDEBAR: NAVIGATION, FILTERS & SEARCH ---
st.sidebar.header("Navigation & Filters")

# External Counter Tool Link
st.sidebar.link_button(
    "⚓ BDO Bartering Item Counter", 
    "https://gemini.google.com/gem/1zm5B-3aPQS1QNhShGUP66-R3P9a8v7o4?usp=sharing",
    use_container_width=True,
    help="Click here to use the external item counter tool."
)

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "Upload your Barter Stock Excel file (.xlsx)", 
    type=["xlsx"]
)

df = load_data(uploaded_file)

if df.empty:
    st.warning("Please upload a valid Excel file with columns: Item Name, Level, Quantity.")
    st.stop()

selected_level = st.sidebar.multiselect(
    "Filter by Item Level",
    options=sorted(df["Level"].dropna().unique()),
    default=sorted(df["Level"].dropna().unique())
)

# Apply level filters for main dashboard elements
filtered_df = df[df["Level"].isin(selected_level)]

st.sidebar.markdown("---")

# Search Inventory in Sidebar (Bypasses active filters to search full inventory)
st.sidebar.markdown("### 🔍 Search Inventory")
search_term = st.sidebar.text_input("Enter item name to check:", key="sidebar_search")

if search_term:
    search_results = df[df["Item Name"].str.contains(search_term.strip(), case=False, na=False)]
    
    if not search_results.empty:
        st.sidebar.dataframe(
            search_results, 
            column_config={
                "Item Name": "Item",
                "Level": "Tier",
                "Quantity": "Stock"
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.sidebar.error(f"No items matching '{search_term}' found.")


# --- MAIN AREA: METRICS / KPIS ---
st.markdown("### 📊 Quick Status")
col1, col2, col3 = st.columns(3)

total_items = len(filtered_df)
low_stock = len(filtered_df[filtered_df["Quantity"] < 5])
out_of_stock = len(filtered_df[filtered_df["Quantity"] == 0])

col1.metric("Total Items Monitored", total_items)
col2.metric("Items Below Par (< 5)", low_stock, delta=-1, delta_color="inverse")
col3.metric("Out of Stock", out_of_stock, delta_color="inverse")

st.markdown("---")


# --- INCREASE FONT SIZE FOR RESTOCK TABLE BY 20% ---
st.markdown(
    """
    <style>
    /* Target the table rows and headers inside the dataframe container */
    div[data-testid="stDataFrame"] table {
        font-size: 25px !important;
    }
    div[data-testid="stDataFrame"] th div p {
        font-size: 25px !important; 
    }
    div[data-testid="stDataFrame"] td div {
        font-size: 25px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --- MAIN AREA: FULL-WIDTH RESTOCK TABLE ---
st.markdown("### 🚨 Items to Restock (Quantity < 5)")

if not filtered_df.empty:
    needs_restock = filtered_df[filtered_df["Quantity"] < 5].sort_values(by="Quantity")
    
    # Rendered natively without columns layout so it takes 100% of the screen width
    st.dataframe(
        needs_restock, 
        column_config={
            "Item Name": "Item",
            "Level": "Tier",
            "Quantity": "Stock"
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No items match your selected tier filters.")