import requests
import urllib3
from utils import convert_excel_date

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_filtered_order_details(order_number, target_date):
    try:
        url = f"https://carepulse-server.g3p.pcf.dell.com/api/getOrderDetails?orderNumber={order_number}"
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return [entry for entry in data if entry.get("CreatedDate", "").startswith(str(target_date))]
        return []
    except requests.RequestException as e:
        print(f"API call failed for order {order_number}: {e}")
        return []
