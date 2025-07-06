# splunk_fetcher.py
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger("SageWatch")

SPLUNK_URL = "https://splunksearch.dell.com/en-US/app/search/search"
SPLUNK_QUERY_TEMPLATE = 'index="esupp_nginx" url="support/order-status/" cookie_dellcemsession="{}"'

def fetch_splunk_data(driver, cookie_value):
    """Fetch Splunk data using Dell CEM session cookie"""
    try:
        # Open new tab for Splunk
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(SPLUNK_URL)
        
        # Wait for page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[@id='search-input']"))
        )
        time.sleep(3)  # Additional stabilization
        
        # Set time range to Last 7 days
        time_picker = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.timerange-picker"))
        time_picker.click()
        
        last_7_days = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Last 7 days')]"))
        )
        last_7_days.click()
        time.sleep(2)
        
        # Enter search query
        search_input = driver.find_element(By.XPATH, "//textarea[@id='search-input']")
        search_input.clear()
        search_input.send_keys(SPLUNK_QUERY_TEMPLATE.format(cookie_value))
        
        # Click search button
        search_button = driver.find_element(By.XPATH, "//button[@title='Search']")
        search_button.click()
        
        # Wait for results
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.events-viewer"))
        )
        time.sleep(5)  # Allow results to populate
        
        # Extract results
        events = driver.find_elements(By.CSS_SELECTOR, "div.event")
        return "\n\n".join([event.text for event in events])
    
    except TimeoutException:
        logger.error("Timed out waiting for Splunk elements")
        return "Splunk data fetch timed out"
    except Exception as e:
        logger.error(f"Splunk fetch error: {str(e)}")
        return f"Splunk fetch error: {str(e)}"
    finally:
        # Close Splunk tab and return to main window
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
