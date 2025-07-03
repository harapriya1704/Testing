from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import yaml
from pathlib import Path
from excel_reader import read_excel_with_required_columns
from file_operations import append_session_to_excel
from carepulse_fetcher import fetch_filtered_order_details
from glassbox_scraper import extract_glassbox_session_data
from utils import convert_excel_date
from logger import logger

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

INPUT_DIR = Path(config["paths"]["input_dir"])
USERNAME = config.get("auth", {}).get("username", "")
PASSWORD = config.get("auth", {}).get("password", "")

class ExcelFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".xlsx"):
            logger.info(f"New file detected: {event.src_path} — processing will start in 2 seconds.")
            time.sleep(2)
            try:
                df = read_excel_with_required_columns(event.src_path)
                logger.info(f"Extracted {len(df)} DSAT rows from {event.src_path}")
                for _, row in df.iterrows():
                    entry = {
                        "fiscal_week": row["Fiscal Week"],
                        "date": row["Date"],
                        "order_number": row["Order Number"],
                        "sat_dissat": row["Sat/Dissat"],
                        "improve_text": row["Improve Text"],
                        "glassbox_link": row["Glassbox Link"]
                    }

                    # Extract session data from Glassbox
                    session_data = extract_glassbox_session_data(entry["glassbox_link"], USERNAME, PASSWORD)
                    entry.update(session_data)

                    # Fetch order details from API
                    excel_date = convert_excel_date(entry["date"])
                    entry["order_details"] = fetch_filtered_order_details(entry["order_number"], excel_date)

                    # Append to output Excel
                    append_session_to_excel(entry)

                logger.info(f"✅ Finished processing {event.src_path}")
            except Exception as e:
                logger.error(f"❌ Error processing {event.src_path}: {e}")

def start_monitor():
    event_handler = ExcelFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INPUT_DIR), recursive=False)
    observer.start()
    logger.info("Folder monitoring started...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitor()
