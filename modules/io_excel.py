from __future__ import annotations
import io, os
import pandas as pd
from typing import Dict, Iterable, Tuple, List, Sequence

# ========== Helpers ==========

def _read_excel_best_sheet(file_like: io.BytesIO, *, engine: str) -> pd.DataFrame:
    """
    Đọc Excel và tự chọn sheet có dữ liệu nhiều nhất.
    """
    file_like.seek(0)
    xls = pd.ExcelFile(file_like, engine=engine)
    best_df = None
    best_size = -1
    for s in xls.sheet_names:
        df = xls.parse(s)
        size = df.shape[0] * df.shape[1]
        if size > best_size:
            best_size = size
            best_df = df
    return best_df if best_df is not None else pd.DataFrame()

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hoá tên cột: strip khoảng trắng đầu/cuối, thay các khoảng trắng liên tiếp = 1 space.
    Không đổi tiếng Việt có dấu để tránh lẫn lộn với báo cáo của bạn.
    """
    df = df.copy()
    df.columns = [(" ".join(str(c).strip().split())) for c in df.columns]
    return df

# ========== Public APIs ==========

def read_any(uploaded_file, sheet: str | int | None = None) -> pd.DataFrame:
    """
    Đọc 1 file người dùng upload (.csv / .xlsx / .xls) -> DataFrame.
    - Nếu là Excel và không chỉ định sheet => tự chọn sheet có dữ liệu nhiều nhất.
    - Gắn thuộc tính df.attrs['source_name'] để biết nguồn.
    """
    name = uploaded_file.name.lower()

    # Đọc bytes để có thể seek nhiều lần (pandas cần)
    raw = uploaded_file.read()
    bio = io.BytesIO(raw)

    if name.endswith(".csv"):
        df = pd.read_csv(bio, encoding_errors="ignore")
    elif name.endswith(".xlsx"):
        if sheet is None:
            df = _read_excel_best_sheet(bio, engine="openpyxl")
        else:
            bio.seek(0)
            df = pd.read_excel(bio, sheet_name=sheet, engine="openpyxl")
    elif name.endswith(".xls"):
        # Cần xlrd trong requirements.txt
        if sheet is None:
            df = _read_excel_best_sheet(bio, engine="xlrd")
        else:
            bio.seek(0)
            df = pd.read_excel(bio, sheet_name=sheet, engine="xlrd")
    else:
        raise ValueError("Chỉ hỗ trợ .xlsx, .xls hoặc .csv")

    df = _normalize_columns(df)
    df.attrs["source_name"] = uploaded_file.name
    return df

def concat_excels(uploaded_files: Sequence, sheet: str | int | None = None,
                  required: Iterable[str] | None = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Hợp nhất nhiều file theo chiều dọc.
    - Bỏ qua file trống/đọc lỗi nhưng trả về danh sách cảnh báo.
    - Nếu 'required' được cung cấp, chỉ nhận những file có đủ cột.
    Trả về: (df_merged, warnings)
    """
    merged = []
    warnings: List[str] = []

    for f in uploaded_files:
        try:
            df = read_any(f, sheet=sheet)
            if df.empty:
                warnings.append(f"{f.name}: sheet rỗng")
                continue
            if required:
                ok, missing = validate_columns(df, required)
                if not ok:
                    warnings.append(f"{f.name}: thiếu cột {', '.join(missing)} — bỏ qua")
                    continue
            # thêm cột nguồn để truy vết
            if "SOURCE_FILE" not in df.columns:
                df["SOURCE_FILE"] = getattr(df, "attrs", {}).get("source_name", f.name)
            merged.append(df)
        except Exception as e:
            warnings.append(f"{f.name}: lỗi đọc — {e}")

    if not merged:
        return pd.DataFrame(), warnings

    # Gộp theo union cột, tự căn chỉnh thiếu cột
    df_all = pd.concat(merged, ignore_index=True, sort=False)
    return df_all, warnings

def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    """
    Ghi nhiều sheet ra 1 file Excel (bytes) để dùng với st.download_button.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        for sheet, df in sheets.items():
            # bảo vệ sheet_name <= 31 ký tự
            safe_sheet = (sheet or "Sheet1")[:31]
            df.to_excel(w, index=False, sheet_name=safe_sheet)
    return buf.getvalue()

def validate_columns(df: pd.DataFrame, required: Iterable[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in required if c not in df.columns]
    return (len(missing) == 0, missing)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
