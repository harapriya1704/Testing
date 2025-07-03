
from datetime import datetime, timedelta
import pandas as pd

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
