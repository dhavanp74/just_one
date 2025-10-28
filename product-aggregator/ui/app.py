# ui/app.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from data_source.api_helper import fetch_combined  # only import this

st.set_page_config(page_title="Product Price Comparator", layout="wide")
st.title("🛒 Product Price Comparison Tool")
st.markdown("Compare product prices across multiple e-commerce categories!")

# Category / query input
category_or_query = st.text_input("Enter product category or search query:", "")

if st.button("Fetch Products"):
    with st.spinner("Fetching products from Flipkart & Amazon..."):
        df = fetch_combined(category_or_query)

    if df.empty:
        st.error("No products found.")
    else:
        st.success(f"✅ Found {len(df)} products!")
        st.dataframe(df.head(20), width='stretch')

        st.markdown("### 🧾 Product Highlights")
        cols = st.columns(2)
        for i, row in enumerate(df.itertuples(), 1):
            with cols[(i-1) % 2]:
                if getattr(row, "image", None):
                    st.image(row.image, width=200, caption=row.source)
                else:
                    st.write(f"📦 {row.brand} (No image)")
                st.markdown(f"**{row.description}**")
                st.markdown(f"💰 {row.price}")
                st.markdown(f"🏷️ {row.tag}")
                st.markdown("---")
