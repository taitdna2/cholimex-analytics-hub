import streamlit as st
import pandas as pd

st.title("👥 Khách hàng tham gia trưng bày")

file = st.file_uploader("Tải danh sách khách hàng tham gia (CSV/XLSX)", type=["csv","xlsx"])
if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    st.write("Trước xử lý:", df.shape)
    # DEMO: chuẩn hóa & loại trùng
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip()
    if "outlet_id" in df.columns:
        df = df.drop_duplicates(subset=["outlet_id"])
    st.write("Sau xử lý:", df.shape)
    st.dataframe(df.head(100), use_container_width=True)
