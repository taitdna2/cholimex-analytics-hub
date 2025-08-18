# modules/utils.py
from pathlib import Path

def init_dirs():
    """
    Tạo và đảm bảo tồn tại các thư mục chuẩn trong project:
      - data/raw: chứa file input gốc tải từ HT DMS
      - data/processed: chứa file trung gian sau khi xử lý
      - data/exports: chứa file kết quả cuối cùng (cho người dùng tải)
      - logs: chứa file log (nếu có)

    Trả về tuple (RAW_DIR, EXPORT_DIR, PROCESSED_DIR, LOGS_DIR)
    """
    RAW_DIR = Path("data/raw")
    EXPORT_DIR = Path("data/exports")
    PROCESSED_DIR = Path("data/processed")
    LOGS_DIR = Path("logs")

    for d in [RAW_DIR, EXPORT_DIR, PROCESSED_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    return RAW_DIR, EXPORT_DIR, PROCESSED_DIR, LOGS_DIR
