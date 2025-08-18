import streamlit as st
import pandas as pd

st.title("📑 Báo cáo trưng bày")

sales = st.file_uploader("1) Bán ra", type=["csv","xlsx"], key="bc_sales")
khach = st.file_uploader("2) DS khách tham gia", type=["csv","xlsx"], key="bc_khach")
posm  = st.file_uploader("3) POSM (tùy chọn)", type=["csv","xlsx"], key="bc_posm")

def read_any(f):
    return pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)

if st.button("Tổng hợp báo cáo"):
    frames = []
    if sales: frames.append(read_any(sales).assign(source="sales"))
    if khach: frames.append(read_any(khach).assign(source="khach"))
    if posm:  frames.append(read_any(posm).assign(source="posm"))
    if not frames:
        st.warning("Chưa chọn dữ liệu.")
        st.stop()
    df = pd.concat(frames, ignore_index=True)
    st.dataframe(df.head(200), use_container_width=True)
    st.success("Demo tổng hợp xong – bạn có thể bổ sung công thức KPI, chuẩn hóa cột…")
