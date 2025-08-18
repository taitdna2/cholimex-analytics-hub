# === BẮT BUỘC: đảm bảo import được "modules/..." khi chạy từ pages/ ===
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]   # thư mục gốc project
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# =====================================================================

import streamlit as st
import os
import pandas as pd

# Import HÀM run(...) từ module của bạn
from modules.thanh_toan_tb.TH_TRA_THUONG import run as merge_run
from modules.thanh_toan_tb.main_TT_tra_thuong import run as main_run
from modules.utils import init_dirs   # <-- import hàm khởi tạo thư mục

# Khởi tạo thư mục chuẩn
RAW_DIR, EXPORT_DIR, PROCESSED_DIR, LOGS_DIR = init_dirs()

st.title("💸 Thanh toán trả thưởng trưng bày")

# ================== BƯỚC 1: HỢP NHẤT FILE HT DMS (tuỳ chọn) ==================
st.markdown("### 1) Hợp nhất file từ HT DMS (tuỳ chọn)")
uploaded_files = st.file_uploader(
    "Tải nhiều file DMS (Excel) để hợp nhất",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files and st.button("📂 Hợp nhất dữ liệu"):
    saved_paths = []
    for f in uploaded_files:
        out_path = RAW_DIR / f.name
        with open(out_path, "wb") as f2:
            f2.write(f.getbuffer())
        saved_paths.append(out_path)
    st.success(f"✅ Đã lưu {len(saved_paths)} file vào {RAW_DIR}")

    try:
        out_merged = RAW_DIR / "output-tra-thuong.xlsx"
        merge_run(input_dir=RAW_DIR, output_path=out_merged)   # gọi hàm run mới
        st.success(f"✅ Hợp nhất xong: `{out_merged}`")
    except Exception as e:
        st.error(f"❌ Lỗi khi hợp nhất: {e}")

st.divider()

# ================== BƯỚC 2: CHẠY TÍNH TRẢ THƯỞNG (MAIN) ==================
st.markdown("### 2) Chạy tính trả thưởng (main)")
input_file = st.file_uploader(
    "Chọn 1 file đầu vào có sheet 'Số tiền đã trả thưởng' (ví dụ: output-tra-thuong.xlsx)",
    type=["xlsx", "xls"],
)

if input_file:
    in_path = RAW_DIR / input_file.name
    with open(in_path, "wb") as f:
        f.write(input_file.getbuffer())
    st.info(f"📄 Đã lưu file vào: `{in_path}`")

    if st.button("▶️ Tính thưởng"):
        try:
            # GỌI HÀM MAIN của bạn
            main_run(
                input_file=in_path,
                output_file="output.xlsx",
                alert_file="alert.xlsx"
            )

            # Di chuyển file kết quả vào exports + nút tải + preview
            out_links = []
            for fn in ["output.xlsx", "alert.xlsx"]:
                p = Path(fn)
                if p.exists():
                    dest = EXPORT_DIR / p.name
                    if dest.exists():  # tránh ghi đè
                        i = 1
                        base, ext = os.path.splitext(p.name)
                        while (EXPORT_DIR / f"{base}_{i}{ext}").exists():
                            i += 1
                        dest = EXPORT_DIR / f"{base}_{i}{ext}"
                    os.replace(p, dest)
                    out_links.append(dest)

            if out_links:
                st.success("✅ Xử lý xong. Xem nhanh & tải file bên dưới.")
                for p in out_links:
                    st.markdown(f"**Tệp:** `{p.name}`")
                    # Preview 100 dòng đầu sheet đầu tiên (nếu đọc được)
                    try:
                        xls = pd.ExcelFile(p)
                        first_sheet = xls.sheet_names[0]
                        df_preview = pd.read_excel(xls, sheet_name=first_sheet).head(100)
                        st.caption(f"Xem nhanh sheet: **{first_sheet}** (100 dòng đầu)")
                        st.dataframe(df_preview, use_container_width=True)
                    except Exception:
                        pass

                    with open(p, "rb") as f:
                        st.download_button(
                            label=f"⬇️ Tải {p.name}",
                            data=f,
                            file_name=p.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{p.name}",
                        )
            else:
                st.warning("Không thấy `output.xlsx` / `alert.xlsx` sau khi chạy.")

        except Exception as e:
            st.error(f"❌ Lỗi khi tính thưởng: {e}")
