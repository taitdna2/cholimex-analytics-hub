import streamlit as st
import pandas as pd

st.title("🧰 POSM")

file = st.file_uploader("Tải dữ liệu POSM trưng bày (CSV/XLSX)", type=["csv","xlsx"])
if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    st.subheader("Tổng quan")
    if "region" in df.columns:
        st.write("Số điểm theo vùng:")
        st.dataframe(df["region"].value_counts().rename_axis("region").reset_index(name="count"))
    if "item" in df.columns:
        st.write("Top vật phẩm POSM:")
        st.dataframe(df["item"].value_counts().head(20).rename_axis("item").reset_index(name="count"))
    st.subheader("Xem nhanh 100 dòng đầu")
    st.dataframe(df.head(100), use_container_width=True)
