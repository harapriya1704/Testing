from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from logger import logger

def extract_glassbox_session_data(glassbox_url, username, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    session_data = {
        "gia_insights": "",
        "Global_DellCEMSessionCookie_CSH": "",
        "Global_MCMID_CSH": "",
        "Client-Sessions": "",
        "Server-Sessions": ""
    }

    try:
        logger.info("Launching browser and navigating to Glassbox login page.")
        driver.get("https://glassbox.dell.com/webinterface/webui/login")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username")))

        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()

        WebDriverWait(driver, 20).until(EC.url_contains("webui"))
        logger.info("Login successful.")

        driver.get(glassbox_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "session-info")))

        # Extract GIA insights
        try:
            gia_element = driver.find_element(By.CLASS_NAME, "session-info")
            session_data["gia_insights"] = gia_element.text
        except Exception as e:
            logger.warning(f"GIA insights not found: {e}")

        # Extract cookies
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie["name"] == "Global_DellCEMSessionCookie_CSH":
                session_data["Global_DellCEMSessionCookie_CSH"] = cookie["value"]
            elif cookie["name"] == "Global_MCMID_CSH":
                session_data["Global_MCMID_CSH"] = cookie["value"]

        # Extract client and server sessions
        try:
            client_sessions = driver.find_elements(By.CLASS_NAME, "client-session")
            session_data["Client-Sessions"] = "; ".join([el.text for el in client_sessions])
        except Exception as e:
            logger.warning(f"Client sessions not found: {e}")

        try:
            server_sessions = driver.find_elements(By.CLASS_NAME, "server-session")
            session_data["Server-Sessions"] = "; ".join([el.text for el in server_sessions])
        except Exception as e:
            logger.warning(f"Server sessions not found: {e}")

    except Exception as e:
        logger.error(f"Error during Glassbox session extraction: {e}")
    finally:
        driver.quit()

    return session_data
