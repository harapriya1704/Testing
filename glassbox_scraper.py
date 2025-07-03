from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config import WAIT_TIMES, GLASSBOX_URL
from file_operations import append_session_to_excel, update_last_row_with_order_details
from selenium.webdriver.edge.options import Options
from api_operations import fetch_filtered_order_details
from utils import convert_excel_date
import subprocess
import time
import json

# All web operation functions from original web_operations.py go here
# (create_silent_edge_driver, wait_for_authentication, extract_gia_insights, etc.)

# Modified process_glassbox_links function:
def process_glassbox_links(data, output_path, driver):
    for index, entry in enumerate(data):
        try:
            # Open new tab
            driver.execute_script("window.open('about:blank', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(entry["glassbox_link"])
            time.sleep(35)

            # ... existing processing logic ...

            # Write to specific output file
            append_session_to_excel(entry, output_path)
            
            # Fetch API data
            order_number = entry.get("order_number")
            excel_date = convert_excel_date(entry.get("date"))
            entry["order_details"] = fetch_filtered_order_details(order_number, excel_date)
            
            update_last_row_with_order_details(entry["order_details"], output_path)

        except Exception as e:
            print(f"Error processing link: {e}")
        finally:
            # Close tab and switch back to main
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    
    return data
