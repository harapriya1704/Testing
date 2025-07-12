import time
from scrapers import gia_insights, expert_view, server_view, cookie_extractor

def scrape_glassbox_session(entry, driver):
    """
    Scrape Glassbox session data for a single entry
    Returns updated entry with Glassbox session data
    """
    try:
        # Open new tab for this session
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(entry["glassbox_link"])
        time.sleep(10)  # Allow page to load

        # Extract GIA Insights
        entry["gia_insights"] = gia_insights.extract_gia_insights(driver)
        gia_insights.close_gia_insights(driver)

        # Extract Expert View (Client Sessions)
        expert_view.click_expert_view_icon(driver)
        expert_view_sessions = expert_view.extract_expert_view_sessions(driver)
        entry["Client-Sessions"] = format_expert_view(expert_view_sessions)

        # Extract Server View (Server Sessions)
        server_view.click_server_view_icon(driver)
        server_view_sessions = server_view.extract_server_view_sessions(driver)
        entry["Server-Sessions"] = format_server_view(server_view_sessions)

        # Extract Cookies
        cookie_extractor.click_topbar_cross_button(driver)
        dell_cookie, mcmid_cookie = cookie_extractor.extract_cookie_values(driver)
        entry["Global_DellCEMSessionCookie_CSH"] = dell_cookie
        entry["Global_MCMID_CSH"] = mcmid_cookie

    except Exception as e:
        print(f"Error scraping Glassbox session: {e}")
        # Add error indicators to the entry
        entry["gia_insights"] = "Error: Scraping failed"
        entry["Client-Sessions"] = "Error: Scraping failed"
        entry["Server-Sessions"] = "Error: Scraping failed"
        entry["Global_DellCEMSessionCookie_CSH"] = ""
        entry["Global_MCMID_CSH"] = ""
    finally:
        # Close tab and switch back to main window
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    
    return entry

def format_expert_view(sessions):
    """Format expert view sessions for output"""
    if isinstance(sessions, list):
        return "\n\n".join([
            f"Title: {s['title']}\nURL: {s['url']}\nDuration: {s['duration']}\nEvents: {s['events']}"
            for s in sessions
        ])
    return sessions

def format_server_view(sessions):
    """Format server view sessions for output"""
    if isinstance(sessions, list):
        return "\n\n".join([
            f"Time: {s['time']}\nURL: {s['url']}\nStatus: {s['status']}\nTotal Time (ms): {s['total_time_ms']}"
            for s in sessions
        ])
    return sessions
