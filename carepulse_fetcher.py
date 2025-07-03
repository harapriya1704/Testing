import requests
import yaml
from utils import convert_excel_date
from logger import logger

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

API_URL = config["api"]["order_details_url"]

def fetch_filtered_order_details(order_number, target_date):
    try:
        url = f"{API_URL}?orderNumber={order_number}"
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return [entry for entry in data if entry.get("CreatedDate", "").startswith(str(target_date))]
        return []
    except requests.RequestException as e:
        logger.error(f"API call failed for order {order_number}: {e}")
        return []
