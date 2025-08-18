import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 Sản lượng / Doanh số theo SKU")

file = st.file_uploader("Tải dữ liệu bán (CSV/XLSX)", type=["csv","xlsx"])
group_cols = st.multiselect("Nhóm theo", ["date","region","channel","sku"], default=["sku"])
value_cols = st.multiselect("Chỉ số", ["qty","price","revenue"], default=["qty","revenue"])

def df_to_excel_bytes(df):
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Pivot")
    buf.seek(0)
    return buf

if file:
    df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    if "revenue" not in df.columns and {"qty","price"}.issubset(df.columns):
        df["revenue"] = df["qty"] * df["price"]
    agg = {c:"sum" for c in value_cols}
    pivot = df.groupby(group_cols, dropna=False).agg(agg).reset_index()
    st.dataframe(pivot.head(200), use_container_width=True)
    st.download_button("⬇️ Tải pivot (Excel)", data=df_to_excel_bytes(pivot), file_name="san_luong_sku.xlsx")
