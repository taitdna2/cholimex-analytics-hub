# pages/1_💸_ThanhToan_TB.py
from __future__ import annotations
# ==== đảm bảo import modules/... ====
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import os, tempfile, shutil
from modules.thanh_toan_tb.TH_TRA_THUONG import run as merge_run
from modules.thanh_toan_tb.main_TT_tra_thuong import run as main_run

st.title("💸 Thanh toán trả thưởng trưng bày")

RAW_DIR = ROOT / "data" / "raw"
EXPORT_DIR = ROOT / "data" / "exports"
for d in [RAW_DIR, EXPORT_DIR, ROOT / "data" / "processed", ROOT / "logs"]:
    d.mkdir(parents=True, exist_ok=True)

# ========== B1. HỢP NHẤT ==========
st.subheader("1) Hợp nhất file từ HT DMS (tuỳ chọn)")
uploaded_files = st.file_uploader(
    "Tải nhiều file DMS (Excel) để hợp nhất",
    type=["xlsx", "xls"],
    accept_multiple_files=True
)

save_mode = st.radio(
    "Chọn cách lưu file upload:",
    ["Dùng tạm (không lưu)", "Lưu vào data/raw"],
    horizontal=True
)

if uploaded_files and st.button("📂 Hợp nhất dữ liệu"):
    # Chọn nơi đặt file đầu vào
    if save_mode == "Dùng tạm (không lưu)":
        work_dir = Path(tempfile.mkdtemp(prefix="merge_tmp_"))
    else:
        work_dir = RAW_DIR

    # Ghi file lên work_dir
    saved_paths = []
    for f in uploaded_files:
        out_path = work_dir / f.name
        with open(out_path, "wb") as g:
            g.write(f.getbuffer())
        saved_paths.append(out_path)

    st.success(f"Đã nhận {len(saved_paths)} file.")

    try:
        out_merged = work_dir / "output-tra-thuong.xlsx"
        merge_run(input_dir=work_dir, output_path=out_merged)
        st.success(f"✅ Hợp nhất xong: `{out_merged}`")

        # Cho phép tải trực tiếp file hợp nhất
        with open(out_merged, "rb") as f:
            st.download_button(
                "⬇️ Tải output-tra-thuong.xlsx",
                data=f.read(),
                file_name="output-tra-thuong.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    except Exception as e:
        st.error(f"❌ Lỗi khi hợp nhất: {e}")

    finally:
        # Nếu là thư mục tạm thì dọn dẹp
        if save_mode == "Dùng tạm (không lưu)":
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

st.divider()

# ========== B2. CHẠY MAIN ==========
st.subheader("2) Chạy tính trả thưởng (main)")
input_file = st.file_uploader(
    "Chọn 1 file đầu vào có sheet 'Số tiền đã trả thưởng' (ví dụ: output-tra-thuong.xlsx)",
    type=["xlsx", "xls"],
)

if input_file:
    # không bắt buộc lưu; dùng tạm file để đọc
    tmp_dir = Path(tempfile.mkdtemp(prefix="main_tmp_"))
    in_path = tmp_dir / input_file.name
    with open(in_path, "wb") as f:
        f.write(input_file.getbuffer())
    st.info(f"Đã nhận file: `{input_file.name}`")

    if st.button("▶️ Tính thưởng"):
        try:
            out_path = tmp_dir / "output.xlsx"
            alert_path = tmp_dir / "alert.xlsx"

            main_run(
                input_file=in_path,
                output_file=out_path,
                alert_file=alert_path
            )

            # Hiển thị & cho tải
            for p in [out_path, alert_path]:
                if p.exists():
                    st.markdown(f"**Tệp tạo:** `{p.name}`")
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
                            f"⬇️ Tải {p.name}",
                            data=f.read(),
                            file_name=p.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"dl_{p.name}"
                        )
                else:
                    st.warning(f"Không thấy file {p.name}")

        except Exception as e:
            st.error(f"❌ Lỗi khi tính thưởng: {e}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
