# 1_💸_ThanhToan_TB.py

# === ĐƯA PROJECT ROOT VÀO sys.path để import "modules/..." ===
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import io
import tempfile
from pathlib import Path
from typing import List, Dict

import pandas as pd
import streamlit as st

# Import 2 hàm run bạn đã có (giữ nguyên logic bên trong)
from modules.thanh_toan_tb.TH_TRA_THUONG import run as merge_run   # Hợp nhất (xuất output-tra-thuong.xlsx)
from modules.thanh_toan_tb.main_TT_tra_thuong import run as main_run  # Tính thưởng (xuất output.xlsx & alert.xlsx)

st.set_page_config(page_title="Thanh toán trả thưởng trưng bày", layout="wide")

# ========= SESSION STATE =========
# Lưu file hợp nhất (bytes) & kết quả tính thưởng (dict tên_file -> bytes)
if "merged_bytes" not in st.session_state:
    st.session_state["merged_bytes"] = None

if "tt_results" not in st.session_state:
    # {"output.xlsx": bytes, "alert.xlsx": bytes}
    st.session_state["tt_results"] = None

# ========= TIÊU ĐỀ =========
st.title("💸 Thanh toán trả thưởng trưng bày")
st.caption("Không lưu file vào đĩa — xử lý trực tiếp trên bộ nhớ và cho tải kết quả.")

# ========= HÀM TIỆN ÍCH (KHÔNG ĐỔI LOGIC) =========
def run_merge_in_memory(files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> bytes:
    """
    Ghi các file upload vào thư mục tạm, gọi merge_run(input_dir, output_path),
    đọc lại bytes của 'output-tra-thuong.xlsx' và trả về.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        for f in files:
            (tmpdir_path / f.name).write_bytes(f.getbuffer())
        out_path = tmpdir_path / "output-tra-thuong.xlsx"
        merge_run(input_dir=tmpdir_path, output_path=out_path)
        return out_path.read_bytes()

def run_main_in_memory(file_bytes: bytes) -> Dict[str, bytes]:
    """
    Gọi main_run nhưng lưu output.xlsx & alert.xlsx vào thư mục tạm,
    rồi đọc lại bytes để trả về (không để lại file nào trên đĩa ứng dụng).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        in_path = tmpdir_p / "input.xlsx"
        out_path = tmpdir_p / "output.xlsx"
        alert_path = tmpdir_p / "alert.xlsx"

        in_path.write_bytes(file_bytes)
        # Gọi hàm main (giữ nguyên logic)
        main_run(input_file=in_path, output_file=out_path, alert_file=alert_path)

        result: Dict[str, bytes] = {}
        if out_path.exists():
            result["output.xlsx"] = out_path.read_bytes()
        if alert_path.exists():
            result["alert.xlsx"] = alert_path.read_bytes()
        return result

# ========= 1) HỢP NHẤT FILE TỪ HT DMS (tuỳ chọn) =========
st.subheader("1) Hợp nhất file từ HT DMS (tuỳ chọn)")
uploaded_many = st.file_uploader(
    "Tải nhiều file DMS (Excel) để hợp nhất → xuất 1 tệp hợp nhất",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

col_merge_btn, col_merge_dl = st.columns([1, 2])
with col_merge_btn:
    if uploaded_many:
        if st.button("📂 Hợp nhất dữ liệu (không lưu ra đĩa)"):
            try:
                merged_bytes = run_merge_in_memory(uploaded_many)
                st.session_state["merged_bytes"] = merged_bytes  # LƯU LẠI ĐỂ KHÔNG MẤT SAU RERUN
                st.success("✅ Đã hợp nhất xong! Tải tệp kết quả bên cạnh.")
            except Exception as e:
                st.error(f"❌ Lỗi khi hợp nhất: {e}")

with col_merge_dl:
    if st.session_state["merged_bytes"]:
        st.download_button(
            "⬇️ Tải file hợp nhất (output-tra-thuong.xlsx)",
            data=st.session_state["merged_bytes"],
            file_name="output-tra-thuong.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_merge_output",
            use_container_width=True,
        )

st.divider()

# ========= 2) CHẠY TÍNH TRẢ THƯỞNG =========
st.subheader("2) Chạy tính trả thưởng (main)")
one_file = st.file_uploader(
    "Chọn 1 file đầu vào có sheet 'Số tiền đã trả thưởng' (vd: output-tra-thuong.xlsx)",
    type=["xlsx", "xls"],
    accept_multiple_files=False
)

# Nút chạy
if one_file:
    if st.button("▶️ Tính thưởng (không lưu ra đĩa)"):
        try:
            results = run_main_in_memory(one_file.getbuffer())
            if not results:
                st.warning("Không tạo được output nào (output.xlsx / alert.xlsx).")
            else:
                # LƯU VÀO SESSION để không mất khi rerun
                st.session_state["tt_results"] = results
                st.success("✅ Xử lý xong! Tải file bên dưới.")
        except Exception as e:
            st.error(f"❌ Lỗi khi tính thưởng: {e}")

# RENDER HAI NÚT TẢI LUÔN LUÔN KHI ĐÃ CÓ KẾT QUẢ
res = st.session_state.get("tt_results") or {}

if res:
    # Preview nhanh output.xlsx (nếu có)
    if "output.xlsx" in res:
        try:
            xls = pd.ExcelFile(io.BytesIO(res["output.xlsx"]))
            # ưu tiên Sheet1 hoặc sheet đầu
            first_sheet = "Sheet1" if "Sheet1" in xls.sheet_names else xls.sheet_names[0]
            df_head = pd.read_excel(xls, sheet_name=first_sheet).head(100)
            st.success("✔️ Xử lý xong! Tải file bên dưới.")
            st.caption("Xem nhanh **Sheet1** (100 dòng đầu)")
            st.dataframe(df_head, use_container_width=True)
        except Exception:
            pass

    c1, c2 = st.columns(2)
    with c1:
        if "output.xlsx" in res:
            st.download_button(
                "⬇️ Tải output.xlsx",
                data=res["output.xlsx"],
                file_name="output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_output_xlsx",
                use_container_width=True,
            )
    with c2:
        if "alert.xlsx" in res:
            st.download_button(
                "⬇️ Tải alert.xlsx",
                data=res["alert.xlsx"],
                file_name="alert.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_alert_xlsx",
                use_container_width=True,
            )
