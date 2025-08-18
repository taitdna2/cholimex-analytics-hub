# modules/ui.py
import streamlit as st

def build_sidebar():
    # Ẩn thanh nav mặc định của Streamlit để tự render menu theo ý mình
    st.markdown("""
    <style>
    /* Ẩn nav mặc định (có tiêu đề 'app') */
    div[data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # --- About (cỡ chữ nhỏ) ---
        st.markdown("""
        <div class="about-box">
          <div class="about-title">ℹ️ About</div>
          <div class="about-item">Tác giả: <strong>Nguyen Anh Tai</strong></div>
          <div class="about-item">Phiên bản: <strong>v0.3</strong></div>
        </div>
        <style>
        [data-testid="stSidebar"] .about-box{
            font-size: 12px; line-height: 1.25; color:#6b7280;
            padding:10px 12px; border-radius:10px; background:#f5f7fb; margin:6px 0 12px 0;
        }
        [data-testid="stSidebar"] .about-title{
            font-weight:600; color:#111827; margin-bottom:4px; font-size:12px;
        }
        [data-testid="stSidebar"] .about-item{ margin:2px 0; }
        </style>
        """, unsafe_allow_html=True)

        # --- Menu (đặt ngay dưới About) ---
        st.markdown("### 📂 Danh mục")
        st.page_link("app.py", label="🏠 Trang chính")
        st.page_link("pages/1_💸_ThanhToan_TB.py", label="💸 Thanh toán trưng bày")
        st.page_link("pages/2_👥_KhachHang_TB.py", label="👥 Khách hàng tham gia trưng bày")
        st.page_link("pages/3_📊_SanLuong_SKU.py", label="📊 Sản lượng / Doanh số theo SKU")
        st.page_link("pages/4_🧰_POSM.py", label="🧰 POSM")
        st.page_link("pages/5_📑_BaoCao_TB.py", label="📑 Báo cáo trưng bày")
        st.page_link("pages/6_⚙️_Khac.py", label="⚙️ Khác")
