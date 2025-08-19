# modules/thanh_toan_tb/TH_TRA_THUONG.py
from __future__ import annotations
import pandas as pd
import os
from typing import Dict, List
from pathlib import Path

# 2 tiêu đề cần lấy – ta sẽ tìm theo kiểu "tương đồng"
TARGET_HEADERS = ["Còn lại", "Số tiền đã trả thưởng"]

def _normalize(s: str) -> str:
    # chữ thường + bỏ khoảng thừa 2 bên
    return str(s).strip().lower()

def _find_header(df: pd.DataFrame, wanted: str) -> str | None:
    """
    Tìm cột tương ứng với 'wanted' theo kiểu tolerant:
    - không phân biệt hoa/thường, bỏ khoảng thừa
    - chấp nhận vài biến thể phổ biến
    """
    wanted_norm = _normalize(wanted)
    variants = {wanted_norm}
    # một vài biến thể hay gặp
    if "còn lại" in wanted_norm:
        variants |= {"con lai", "con_lai"}
    if "số tiền đã trả thưởng" in wanted_norm:
        variants |= {
            "so tien da tra thuong", "số tiền đã tt", "so tien da tt",
            "so tien da tra", "số tiền đã trả"
        }

    norm_map = {_normalize(c): c for c in df.columns}
    for v in variants:
        if v in norm_map:
            return norm_map[v]
    # fallback: tìm cột chứa cụm từ
    for norm, raw in norm_map.items():
        if all(tok in norm for tok in wanted_norm.split()):
            return raw
    return None

def run(input_dir: str | Path = "data/raw", output_path: str | Path = "output-tra-thuong.xlsx"):
    """
    Hợp nhất các file Excel trong input_dir → 1 file Excel có 2 sheet:
    - 'Còn lại'
    - 'Số tiền đã trả thưởng'
    (nếu thiếu cột sẽ bỏ qua file đó và ghi chú ra console)
    """
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir not found: {input_dir}")

    cwd_old = Path.cwd()
    os.chdir(input_dir)  # Giữ logic “đọc trong thư mục” cũ

    try:
        def build_sheet_for(header_label: str) -> pd.DataFrame:
            data: Dict[str, List[str]] = {}
            files = [f for f in os.listdir() if f.endswith((".xlsx", ".xls")) and not f.startswith("~$")]
            for filename in files:
                # Đọc .xlsx / .xls (xlrd cho xls)
                try:
                    xls = pd.ExcelFile(filename, engine=None)  # pandas tự chọn, với .xls cần xlrd
                    df = pd.read_excel(xls, xls.sheet_names[0], skiprows=1, engine=None)
                except Exception as e:
                    print(f"[WARN] Không đọc được '{filename}': {e}")
                    continue

                col = _find_header(df, header_label)
                if not col:
                    print(f"[WARN] '{filename}' thiếu cột '{header_label}', bỏ qua.")
                    continue

                # Lọc các dòng col != 0 (an toàn với NaN)
                try:
                    mask = df[col].fillna(0) != 0
                    _data = df.loc[mask].to_dict()
                except Exception as e:
                    print(f"[WARN] Lỗi lọc dữ liệu '{filename}' ({header_label}): {e}")
                    continue

                for k, v in _data.items():
                    data.setdefault(k, [])
                    data[k].extend(list(v.values()))

                # Ghi tên file vào cột trống "" (đúng với logic cũ)
                if "STT" in _data and len(_data["STT"]) == 0:
                    print(f"[INFO] File '{filename}' không có dòng hợp lệ cho '{header_label}'.")
                    continue
                data.setdefault("", [])
                count_rows = len(_data[next(iter(_data))]) if _data else 0
                data[""].extend([filename] + [""] * (max(count_rows - 1, 0)))

            return pd.DataFrame(data)

        sheets = [build_sheet_for(lbl) for lbl in TARGET_HEADERS]
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            for df, name in zip(sheets, TARGET_HEADERS):
                df.to_excel(writer, sheet_name=name, index=False)

        print(f"✅ Đã tạo file {output_path}")
    finally:
        os.chdir(cwd_old)

if __name__ == "__main__":
    run()
