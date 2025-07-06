from datetime import datetime, timedelta
import pandas as pd
from logger import logger
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def fetch_filtered_order_details(order_number, target_date):
    try:
        url = f"https://carepulse-server.g3p.pcf.dell.com/api/getOrderDetails?orderNumber={order_number}"
        logger.debug(f"Order Number: {order_number}, Target Date: {target_date}")
        logger.debug(f"Calling API: {url}")

        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            filtered_data = [
                entry for entry in data
                if entry.get("CreatedDate", "")[:10] == str(target_date)
            ]

            if not filtered_data:
                message = f"No Carepulse logs on {target_date}"
                logger.info(f"{message} for order {order_number}")
                return message

            logger.info(f"Successfully retrieved Carepulse logs for order {order_number} on {target_date}")
            return filtered_data

        return f"No Carepulse logs on {target_date}"

    except requests.RequestException as e:
        logger.error(f"API call failed for order {order_number}: {e}", exc_info=True)
        return f"No Carepulse logs on {target_date}"
