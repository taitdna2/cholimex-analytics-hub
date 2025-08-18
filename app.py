# app.py
import streamlit as st
from PIL import Image
from io import BytesIO
import base64

# ========== CONFIG ==========
st.set_page_config(
    page_title="CHOLIMEX ANALYTICS HUB",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",   # hiện sidebar
)

from modules.ui import build_sidebar
build_sidebar()

# ========== CSS (KHÔNG ẩn sidebar) ==========
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.hub-title { margin: 0; }
.hub-caption { color:#6b7280; margin: 2px 0 0 0; }
</style>
""", unsafe_allow_html=True)

# ========== Logo (Base64) ==========
def load_logo_base64(path="assets/cholimex_logo.png", height=92):
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    r = height / img.height
    img = img.resize((int(img.width * r), height))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8"), height

b64, h = load_logo_base64()

# ========== Header ==========
st.markdown(
    f"""
<div style="display:flex;align-items:center;gap:14px;">
  <img src="data:image/png;base64,{b64}" style="height:{h}px;object-fit:contain;" />
  <div>
    <h1 class="hub-title">CHOLIMEX ANALYTICS HUB</h1>
    <span style="color:#888;">© Nguyen Anh Tai</span>
    <div class="hub-caption">Xử lý dữ liệu: upload • clean • merge • KPI • chart • export</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.divider()

# ========== Main content: Danh mục ==========
st.subheader("📂 Danh mục")
st.page_link("pages/1_💸_ThanhToan_TB.py", label="💸 Thanh toán trả thưởng trưng bày")
st.page_link("pages/2_👥_KhachHang_TB.py", label="👥 Khách hàng tham gia trưng bày")
st.page_link("pages/3_📊_SanLuong_SKU.py", label="📊 Sản lượng / Doanh số theo SKU")
st.page_link("pages/4_🧰_POSM.py", label="🧰 POSM")
st.page_link("pages/5_📑_BaoCao_TB.py", label="📑 Báo cáo trưng bày")
st.page_link("pages/6_⚙️_Khac.py", label="⚙️ Khác")

st.info("Chọn một mục ở trên hoặc dùng menu bên trái để vào trang chi tiết.")

