import pandas as pd
import yaml
from logger import logger

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

REQUIRED_COLUMNS = set(config["excel"]["required_columns"])

def read_excel_with_required_columns(file_path):
    logger.info(f"Reading Excel file: {file_path}")
    df = pd.read_excel(file_path, engine="openpyxl")
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    df_filtered = df[list(REQUIRED_COLUMNS)]
    df_filtered = df_filtered[
        df_filtered["Sat/Dissat"].astype(str).str.strip().str.upper() == "DSAT"
    ]
    df_filtered = df_filtered[df_filtered["Order Number"].notna()]
    return df_filtered
