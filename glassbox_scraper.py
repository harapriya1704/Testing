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
from carepulse_fetcher import fetch_filtered_order_details
from utils import convert_excel_date
from file_operations import update_last_row_with_summary
from llm_analyzer import LLMAnalyser
import subprocess
import time
import json


def create_silent_edge_driver():
    options = Options()
    options.add_argument("--headless=new")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.set_capability("ms:loggingPrefs", {"browser": "OFF", "performance": "OFF"})
    service = Service(EdgeChromiumDriverManager().install())
    service.creationflags = subprocess.CREATE_NO_WINDOW
    driver = webdriver.Edge(service=service, options=options)
    return driver

def wait_for_authentication(driver, timeout=30):
    try:
        print(" Waiting for authentication to complete...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Recorded Sessions')]"))
        )
        print(" Authentication complete.")
    except TimeoutException:
        print(" Please check if login was successful.")

def extract_gia_insights(driver):
    try:
        WebDriverWait(driver, WAIT_TIMES["PAGE_LOAD"]).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        WebDriverWait(driver, WAIT_TIMES["SHORT"]).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'GIA Insights')]"))
        ).click()
        insights_container = WebDriverWait(driver, WAIT_TIMES["GIA_LOAD"] + 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'insights-body')]"))
        )
        previous_length = 0
        stable_count = 0
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            current_text = driver.execute_script("return arguments[0].innerText;", insights_container)
            current_length = len(current_text)
            if current_length == previous_length:
                stable_count += 1
            else:
                stable_count = 0
                previous_length = current_length
            if stable_count >= 5:
                break
            time.sleep(1)
        return current_text
    except Exception as e:
        print("GIA Insights extraction failed:", str(e))
        return ""

def close_gia_insights(driver):
    print("Attempting to close GIA Insights popover...")
    try:
        print("Trying fallback: clicking GIA Insights button again...")
        toggle_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'GIA Insights')]"))
        )
        try:
            toggle_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", toggle_btn)
        print(" Closed GIA Insights popover by toggling the button.")
        time.sleep(2)
        return
    except Exception as e:
        print(" Fallback toggle failed — GIA Insights popover could not be closed:", str(e))

def click_expert_view_icon(driver):
    try:
        expert_view_xpath = "//button[.//gb-icon[@aria-label='expert-view']]"
        elements = driver.find_elements(By.XPATH, expert_view_xpath)
        print(f"🔍 Found {len(elements)} Expert View button(s).")
        if not elements:
            print(" No Expert View button found.")
            return
        expert_view_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, expert_view_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", expert_view_btn)
        driver.execute_script("arguments[0].click();", expert_view_btn)
        print(" Clicked the Expert View icon.")
        time.sleep(10)
    except Exception as e:
        print(" Failed to click the Expert View icon:", str(e))

def extract_expert_view_sessions(driver):
    try:
        print(" Extracting Expert View session entries...")
        time.sleep(2)

        session_blocks = driver.find_elements(By.XPATH, "//ul[@id='cls_tree_pages']/li")

        extracted_data = []

        for block in session_blocks:
            try:
                full_text = block.text.strip()

                try:
                    url = block.find_element(By.XPATH, ".//a").get_attribute("href")
                except:
                    url = ""

                lines = full_text.split("\n")
                title = lines[0] if lines else ""
                duration = ""
                events = ""

                for line in lines:
                    if ":" in line and len(line.strip()) <= 8:
                        duration = line.strip()
                    elif "event" in line.lower():
                        events = line.strip()

                extracted_data.append({
                    "title": title,
                    "url": url,
                    "duration": duration,
                    "events": events
                })

            except Exception as inner_e:
                print("⚠️ Skipped a session entry due to missing data:", str(inner_e))

        print(f" Extracted {len(extracted_data)} session entries from Expert View.")
        return extracted_data

    except Exception as e:
        print(" Failed to extract Expert View sessions:", str(e))
        return []


def click_server_view_icon(driver):
    try:
        print(" Switching to Server View...")
        server_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "serverSideBtn"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", server_btn)
        driver.execute_script("arguments[0].click();", server_btn)
        print(" Clicked the Server View button.")
        time.sleep(5)

        
        print(" Clicking 'Errors Only' filter button...")
        errors_only_btn = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filterBtn') and contains(@class, 'typeErrors')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", errors_only_btn)
        driver.execute_script("arguments[0].click();", errors_only_btn)
        print(" Clicked the 'Errors Only' button.")
        time.sleep(5)

    except Exception as e:
        print(" Failed to click the Server View or Errors Only button:", str(e))



def extract_server_view_sessions(driver):
    try:
        print(" Extracting Server View session entries...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "hit_line"))
        )
        time.sleep(2)

        rows = driver.find_elements(By.CSS_SELECTOR, "div.hit_line.data_line")
        extracted_data = []

        for i, row in enumerate(rows):
            try:
                if not row.is_displayed():
                    continue  

                cells = row.find_elements(By.CLASS_NAME, "data_line_cell")

                if len(cells) < 4:
                    continue  

                time_val = cells[0].find_element(By.TAG_NAME, "span").text.strip()

                url = cells[1].get_attribute("title").strip()

                status = cells[2].find_element(By.TAG_NAME, "span").text.strip()
                total_time = cells[3].find_element(By.TAG_NAME, "span").text.strip()

                if not status and not total_time:
                    continue  

                extracted_data.append({
                    "time": time_val,
                    "url": url,
                    "status": status,
                    "total_time_ms": total_time
                })

            except Exception:
                continue 

        if not extracted_data:
            print("ℹ No error sessions found after filtering.")
            return "No error sessions found."

        print(f" Extracted {len(extracted_data)} server session entries.")
        return extracted_data

    except Exception as e:
        print(" Failed to extract Server View sessions:", str(e))
        return "No error sessions found."


def click_topbar_cross_button(driver):
    try:
        cross_btn_xpath = "//gb-icon[@class='right-panel-icon core-clickable-state ng-scope gbi gbi-close-xs' and @aria-label='close-xs']"
        cross_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, cross_btn_xpath))
        )
        driver.execute_script("arguments[0].click();", cross_btn)
        print(" Clicked the top-bar cross button next to the settings icon.")
        time.sleep(3)
    except Exception as e:
        print(" Failed to click the top-bar cross button:", str(e))

def extract_cookie_values(driver):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"🔄 Attempt {attempt + 1} to extract cookie values...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table"))
            )
            time.sleep(2)
            driver.execute_script("""
                const tableContainer = document.querySelector('.table-container, .gb-table-container, .scrollable-table');
                if (tableContainer) {
                    tableContainer.scrollLeft = tableContainer.scrollWidth;
                }
            """)
            time.sleep(2)
            dell_cookie_xpath = "(//td[contains(@class, 'Global_DellCEMSessionCookie_CSH')]//span)[1]"
            mcmid_cookie_xpath = "(//td[contains(@class, 'Global_MCMID_CSH')]//span)[1]"
            dell_cookie_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, dell_cookie_xpath))
            )
            mcmid_cookie_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, mcmid_cookie_xpath))
            )
            dell_cookie = dell_cookie_element.text.strip()
            mcmid_cookie = mcmid_cookie_element.text.strip()
            return dell_cookie, mcmid_cookie
        except TimeoutException as e:
            print(f" Timeout on attempt {attempt + 1}: {str(e)}")
            time.sleep(2)
        except Exception as e:
            print(f" Unexpected error on attempt {attempt + 1}: {str(e)}")
            break
    print(" All attempts to extract cookie values failed.")
    return "", ""



# Modified process_glassbox_links function:
def process_glassbox_links(data, output_path, driver):
    analyser = LLMAnalyser()
    for index, entry in enumerate(data):
        try:
            # Open new tab
            driver.execute_script("window.open('about:blank', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(entry["glassbox_link"])
            time.sleep(35)

            entry["gia_insights"] = extract_gia_insights(driver)
            close_gia_insights(driver)

            click_expert_view_icon(driver)
            expert_view_sessions = extract_expert_view_sessions(driver)
            entry["Client-Sessions"] = "\n\n".join([
                f"Title: {s['title']}\nURL: {s['url']}\nDuration: {s['duration']}\nEvents: {s['events']}"
                for s in expert_view_sessions
            ]) if isinstance(expert_view_sessions, list) else expert_view_sessions

            click_server_view_icon(driver)
            server_view_sessions = extract_server_view_sessions(driver)
            if isinstance(server_view_sessions, str):
                entry["Server-Sessions"] = server_view_sessions  
            else:
                entry["Server-Sessions"] = "\n\n".join([
                    f"Time: {s['time']}\nURL: {s['url']}\nStatus: {s['status']}\nTotal Time (ms): {s['total_time_ms']}"
                    for s in server_view_sessions
                ])

            click_topbar_cross_button(driver)
            dell_cookie, mcmid_cookie = extract_cookie_values(driver)
            entry["Global_DellCEMSessionCookie_CSH"] = dell_cookie
            entry["Global_MCMID_CSH"] = mcmid_cookie

            
            append_session_to_excel(entry, output_path)
            
            # Fetch API data
            order_number = entry.get("order_number")
            excel_date = convert_excel_date(entry.get("date"))
            entry["order_details"] = fetch_filtered_order_details(order_number, excel_date)
            
            update_last_row_with_order_details(entry["order_details"], output_path)

            analysis_context = {
                "gia_insights": entry.get("gia_insights", ""),
                "Client-Sessions": entry.get("Client-Sessions", ""),
                "Server-Sessions": entry.get("Server-Sessions", ""),
                "order_details": entry.get("order_details", {}),
                "improve_text": entry.get("improve_text", "")
            }

            entry["summary"] = analyser.analyze_dsat(analysis_context)

            update_last_row_with_summary(entry["summary"], output_path)

        except Exception as e:
            print(f"Error processing link: {e}")
        finally:
            # Close tab and switch back to main
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    
    return data
