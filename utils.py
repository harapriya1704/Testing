from datetime import datetime, timedelta
import pandas as pd
import os
import time
from pathlib import Path
from logger import logger
from config import INPUT_DIR

def convert_excel_date(excel_date):
    if isinstance(excel_date, (int, float)):
        return (datetime(1899, 12, 30) + timedelta(days=excel_date)).date()
    elif isinstance(excel_date, datetime):
        return excel_date.date()
    elif isinstance(excel_date, str):
        try:
            return pd.to_datetime(excel_date).date()
        except:
            return None
    return None

def wait_until_file_is_ready(file_path, timeout=10):
    """Wait until the file size stops changing, indicating it's fully written."""
    last_size = -1
    stable_count = 0
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_size = os.path.getsize(file_path)
        if current_size == last_size:
            stable_count += 1
            if stable_count >= 2:  # stable for 2 checks (~2 seconds)
                return True
        else:
            stable_count = 0
        last_size = current_size
        time.sleep(1)
    return False
