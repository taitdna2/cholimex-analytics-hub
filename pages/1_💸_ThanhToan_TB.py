# pages/1_💸_ThanhToan_TB.py
from __future__ import annotations
from pathlib import Path
import sys
import io
import tempfile
from typing import Any, List, Dict

import streamlit as st
import pandas as pd

# === Đưa project root vào sys.path để import "modules/..." ===
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import 2 hàm run bạn đã có
from modules.thanh_toan_tb.TH_TRA_THUONG import run as merge_run      # hợp nhất nhiều file DMS
from modules.thanh_toan_tb.main_TT_tra_thuong import run as main_run  # tính trả thưởng

st.set_page_config(page_title="💸 Thanh toán trả thưởng trưng bày", layout="wide")
st.title("💸 Thanh toán trả thưởng trưng bày")
st.caption("Không lưu file vào repo — xử lý trong thư mục tạm & trả kết quả về cho người dùng.")

# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------
def _bytes_to_excel_preview(xlsx_bytes: bytes, n_rows: int = 100) -> None:
    """Hiển thị preview sheet đầu tiên nếu đọc được."""
    try:
        xls = pd.ExcelFile(io.BytesIO(xlsx_bytes))
        first_sheet = xls.sheet_names[0]
        df_head = pd.read_excel(xls, sheet_name=first_sheet).head(n_rows)
        st.caption(f"Xem nhanh **{first_sheet}** ({len(df_head)} dòng đầu)")
        st.dataframe(df_head, use_container_width=True)
    except Exception:
        pass

def run_merge_in_memory(files: List[Any]) -> bytes:
    """
    Ghi các UploadedFile vào thư mục tạm (chỉ tồn tại trong runtime),
    gọi merge_run(input_dir=..., output_path=...), rồi trả về bytes của file kết quả.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        for f in files:
            # reset về đầu rồi ghi ra file tạm
            f.seek(0)
            (tmpdir_p / f.name).write_bytes(f.read())
        out_path = tmpdir_p / "output-tra-thuong.xlsx"
        # CHÚ Ý: giữ đúng tên tham số như hàm của bạn đang dùng
        merge_run(input_dir=tmpdir_p, output_path=out_path)
        return out_path.read_bytes()

def run_main_in_memory(file_bytes: bytes) -> Dict[str, bytes]:
    """
    Gọi main_run(input_file=..., output_file=..., alert_file=...) trong thư mục tạm,
    rồi trả về dict tên file -> bytes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        in_path = tmpdir_p / "input.xlsx"
        out_path = tmpdir_p / "output.xlsx"
        alert_path = tmpdir_p / "alert.xlsx"

        in_path.write_bytes(file_bytes)
        main_run(input_file=in_path, output_file=out_path, alert_file=alert_path)

        result: Dict[str, bytes] = {}
        if out_path.exists():
            result["output.xlsx"] = out_path.read_bytes()
        if alert_path.exists():
            result["alert.xlsx"] = alert_path.read_bytes()
        return result

# ------------------------------------------------------------
# 1) HỢP NHẤT FILE TỪ HT DMS (tuỳ chọn)
# ------------------------------------------------------------
st.header("1) Hợp nhất file từ HT DMS (tuỳ chọn)")
st.write("Tải **nhiều file** DMS (.xls/.xlsx) để hợp nhất → xuất 1 tệp `output-tra-thuong.xlsx`.")

with st.form("merge_form", clear_on_submit=False):
    uploaded_many = st.file_uploader(
        "Chọn nhiều file DMS",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        key="merge_files"
    )
    do_merge = st.form_submit_button("📂 Hợp nhất dữ liệu (không lưu ra đĩa)")

if do_merge:
    if not uploaded_many:
        st.warning("Chưa chọn file nào.")
    else:
        with st.spinner("Đang hợp nhất..."):
            try:
                merged_bytes = run_merge_in_memory(uploaded_many)
                st.success("✅ Đã hợp nhất xong! Tải tệp kết quả bên dưới.")
                _bytes_to_excel_preview(merged_bytes, n_rows=100)
                st.download_button(
                    "⬇️ Tải file hợp nhất (output-tra-thuong.xlsx)",
                    data=merged_bytes,
                    file_name="output-tra-thuong.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_merge"
                )
            except Exception as e:
                st.error(f"❌ Lỗi khi hợp nhất: {e}")

st.divider()

# ------------------------------------------------------------
# 2) CHẠY TÍNH TRẢ THƯỞNG (đầu vào 1 file)
# ------------------------------------------------------------
st.header("2) Chạy tính trả thưởng (main)")
st.write("Chọn 1 file đầu vào có sheet phù hợp (ví dụ `output-tra-thuong.xlsx`).")

with st.form("main_form", clear_on_submit=False):
    one_file = st.file_uploader(
        "Chọn 1 file đầu vào (.xls/.xlsx)",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="main_file"
    )
    do_main = st.form_submit_button("▶️ Tính thưởng (không lưu ra đĩa)")

if do_main:
    if not one_file:
        st.warning("Chưa chọn file đầu vào.")
    else:
        with st.spinner("Đang tính thưởng..."):
            try:
                one_file.seek(0)
                results = run_main_in_memory(one_file.read())
                if not results:
                    st.warning("Không tạo được output nào (output.xlsx/alert.xlsx).")
                else:
                    st.success("✅ Xử lý xong! Tải file bên dưới.")
                    # Preview output nếu có
                    if "output.xlsx" in results:
                        _bytes_to_excel_preview(results["output.xlsx"], n_rows=100)
                    # Nút tải
                    for name, bts in results.items():
                        st.download_button(
                            f"⬇️ Tải {name}",
                            data=bts,
                            file_name=name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{name}"
                        )
            except Exception as e:
                st.error(f"❌ Lỗi khi tính thưởng: {e}")

# Gợi ý nhỏ
with st.expander("⚙️ Lưu ý & khắc phục sự cố"):
    st.markdown("""
- Nếu file DMS của bạn là **.xls (97-2003)**, đảm bảo `requirements.txt` có `xlrd==2.0.1`.
- Hãy kiểm tra lại các sheet/định dạng đầu vào khớp với yêu cầu trong `modules/thanh_toan_tb/*`.
- App **không ghi** vào `data/raw` hay repo; mọi I/O đều ở thư mục tạm.
    """)
