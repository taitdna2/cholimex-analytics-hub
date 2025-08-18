# modules/thanh_toan_tb/TH_TRA_THUONG.py
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd

CONFIG = ["Còn lại", "Số tiền đã trả thưởng"]

def run(input_dir: str | Path = "data/raw",
        output_path: str | Path = "data/raw/output-tra-thuong.xlsx"):
    """
    Hợp nhất tất cả file Excel trong input_dir và xuất ra 1 file Excel.
    - KHÔNG đổi CWD; dùng đường dẫn tuyệt đối
    - Luôn tạo thư mục cha của output trước khi ghi
    """
    input_dir = Path(input_dir).resolve()
    output_path = Path(output_path).resolve()

    # đảm bảo thư mục cha tồn tại
    output_path.parent.mkdir(parents=True, exist_ok=True)

    def get_data(config: str):
        data: Dict[str, List[str]] = {}
        for p in sorted(input_dir.iterdir()):
            if not (p.suffix.lower() in [".xlsx", ".xls"]):
                continue
            # đọc sheet đầu, bỏ 1 dòng header như logic gốc
            file = pd.ExcelFile(str(p))
            df = pd.read_excel(file, file.sheet_names[0], skiprows=1)

            _data: Dict[str, Dict[int, str]] = df[df[config] != 0].to_dict()
            for k, v in _data.items():
                data.setdefault(k, [])
                data[k].extend(list(v.values()))

            if len(_data.get("STT", {})) == 0:
                print(f'File "{p.name}" không có "{config}"!\n')
                continue

            data.setdefault("", [])
            data[""].extend([p.name] + [""] * (len(list(_data.get("STT", {}).values())) - 1))
        return data

    dfs = [pd.DataFrame(get_data(config)) for config in CONFIG]

    # dùng str(output_path) + engine xlsxwriter
    with pd.ExcelWriter(str(output_path), engine="xlsxwriter") as writer:
        for df, config in zip(dfs, CONFIG):
            df.to_excel(writer, sheet_name=config, index=False)

    print(f"✅ Đã tạo file {output_path}")

if __name__ == "__main__":
    run()
