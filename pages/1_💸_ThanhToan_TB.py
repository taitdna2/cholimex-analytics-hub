# === ĐƯA PROJECT ROOT VÀO sys.path để import "modules/..." ===
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import io
import os
import zipfile
import streamlit as st
import pandas as pd
from typing import List

# Import 2 hàm run bạn đã có (giữ nguyên logic bên trong)
from modules.thanh_toan_tb.TH_TRA_THUONG import run as merge_run   # hợp nhất
from modules.thanh_toan_tb.main_TT_tra_thuong import run as main_run  # tính thưởng

st.title("💸 Thanh toán trả thưởng trưng bày")
st.caption("Không lưu file vào đĩa — xử lý trực tiếp trên bộ nhớ và cho tải kết quả.")

# ====== 1) HỢP NHẤT FILE TỪ HT DMS (tuỳ chọn, không ghi data/raw) ======
st.subheader("1) Hợp nhất file từ HT DMS (tuỳ chọn)")
uploaded_many = st.file_uploader(
    "Tải nhiều file DMS (Excel) để hợp nhất → xuất 1 tệp hợp nhất",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

def run_merge_in_memory(files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> bytes:
    """
    Dùng tạm thư mục ảo trong zipfs để giữ nguyên logic merge_run (nếu bên trong cần os.listdir()),
    nhưng ta sẽ không ghi ra đĩa thật: tạo 1 zip in-memory, mount tạm, hoặc
    đơn giản hơn: ghi các file vào 1 TemporaryDirectory rồi xóa ngay sau dùng.
    Ở đây dùng TemporaryDirectory cho dễ hiểu.
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Lưu từng file upload vào thư mục tạm (chỉ tồn tại trong vòng đời request)
        for f in files:
            (tmpdir / f.name).write_bytes(f.getbuffer())
        # Gọi merge_run với input_dir là thư mục tạm & output_path là file tạm trong thư mục đó
        out_path = tmpdir / "output-tra-thuong.xlsx"
        merge_run(input_dir=tmpdir, output_path=out_path)
        return out_path.read_bytes()  # trả về bytes của file kết quả

if uploaded_many:
    if st.button("📂 Hợp nhất dữ liệu (không lưu ra đĩa)"):
        try:
            merged_bytes = run_merge_in_memory(uploaded_many)
            st.success("✅ Đã hợp nhất xong! Tải tệp kết quả bên dưới.")
            st.download_button(
                "⬇️ Tải file hợp nhất (output-tra-thuong.xlsx)",
                data=merged_bytes,
                file_name="output-tra-thuong.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.error(f"❌ Lỗi khi hợp nhất: {e}")

st.divider()

# ====== 2) CHẠY TÍNH TRẢ THƯỞNG (đầu vào là 1 file, xử lý trên bộ nhớ) ======
st.subheader("2) Chạy tính trả thưởng (main)")
one_file = st.file_uploader(
    "Chọn 1 file đầu vào có sheet 'Số tiền đã trả thưởng' (vd: output-tra-thuong.xlsx)",
    type=["xlsx", "xls"], accept_multiple_files=False
)

def run_main_in_memory(file_bytes: bytes) -> dict:
    """
    Gọi main_run nhưng lưu output.xlsx & alert.xlsx vào thư mục tạm,
    rồi đọc lại bytes để trả về (không để lại file nào trên đĩa ứng dụng).
    """
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_p = Path(tmpdir)
        in_path = tmpdir_p / "input.xlsx"
        out_path = tmpdir_p / "output.xlsx"
        alert_path = tmpdir_p / "alert.xlsx"

        in_path.write_bytes(file_bytes)
        # Gọi hàm main của bạn
        main_run(input_file=in_path, output_file=out_path, alert_file=alert_path)

        result = {}
        if out_path.exists():
            result["output.xlsx"] = out_path.read_bytes()
        if alert_path.exists():
            result["alert.xlsx"] = alert_path.read_bytes()
        return result

if one_file:
    if st.button("▶️ Tính thưởng (không lưu ra đĩa)"):
        try:
            results = run_main_in_memory(one_file.getbuffer())
            if not results:
                st.warning("Không tạo được output nào (output.xlsx / alert.xlsx).")
            else:
                st.success("✅ Xử lý xong! Tải file bên dưới.")
                # Cho tải từng file; đồng thời nếu có output.xlsx, preview sheet đầu
                for name, bts in results.items():
                    if name == "output.xlsx":
                        try:
                            xls = pd.ExcelFile(io.BytesIO(bts))
                            first_sheet = xls.sheet_names[0]
                            df_head = pd.read_excel(xls, sheet_name=first_sheet).head(100)
                            st.caption(f"Xem nhanh **{name}** – sheet đầu: **{first_sheet}** (100 dòng)")
                            st.dataframe(df_head, use_container_width=True)
                        except Exception:
                            pass

                    st.download_button(
                        f"⬇️ Tải {name}",
                        data=bts,
                        file_name=name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{name}",
                    )
        except Exception as e:
            st.error(f"❌ Lỗi khi tính thưởng: {e}")
