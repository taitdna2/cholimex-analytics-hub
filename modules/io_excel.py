from __future__ import annotations
import io, os
import pandas as pd
from typing import Dict, Iterable, Tuple, List

def read_any(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    elif name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    else:
        raise ValueError("Chỉ hỗ trợ .xlsx hoặc .csv")

def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as w:
        for sheet, df in sheets.items():
            df.to_excel(w, index=False, sheet_name=(sheet or "Sheet1")[:31])
    return buf.getvalue()

def validate_columns(df: pd.DataFrame, required: Iterable[str]) -> Tuple[bool, List[str]]:
    missing = [c for c in required if c not in df.columns]
    return (len(missing) == 0, missing)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
