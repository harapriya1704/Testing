import json
from openpyxl import Workbook, load_workbook
import os
import yaml
from logger import logger

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

OUTPUT_PATH = config["paths"]["output_excel"]

def initialize_output_excel():
    wb = Workbook()
    ws = wb.active
    headers = [
        "Fiscal Week", "Date", "Order Number", "Sat/Dissat", "Improve Text",
        "GIA Insights", "Global_DellCEMSessionCookie_CSH", "Global_MCMID_CSH",
        "Client-Sessions", "Server-Sessions", "Order Details"
    ]
    ws.append(headers)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    wb.save(OUTPUT_PATH)
    logger.info(f"Initialized output Excel at {OUTPUT_PATH}")

def append_session_to_excel(entry):
    if not os.path.exists(OUTPUT_PATH):
        initialize_output_excel()

    wb = load_workbook(OUTPUT_PATH)
    ws = wb.active

    row = [
        entry.get("fiscal_week", ""),
        entry.get("date", ""),
        entry.get("order_number", ""),
        entry.get("sat_dissat", ""),
        entry.get("improve_text", ""),
        entry.get("gia_insights", ""),
        entry.get("Global_DellCEMSessionCookie_CSH", ""),
        entry.get("Global_MCMID_CSH", ""),
        entry.get("Client-Sessions", ""),
        entry.get("Server-Sessions", ""),
        json.dumps(entry.get("order_details", {}))
    ]
    ws.append(row)
    wb.save(OUTPUT_PATH)
    logger.info(f"Appended session for order {entry.get('order_number')} to Excel.")
