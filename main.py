from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import os

import json

def load_urls():
    """Reads URLs from urls.json and merges with environment variable URLs."""
    urls = []
    
    # Try to load from urls.json
    try:
        with open("urls.json", "r") as f:
            urls = json.load(f)
            if not isinstance(urls, list):
                print("Warning: urls.json doesn't contain a list. Using empty list.")
                urls = []
    except FileNotFoundError:
        print("urls.json not found. Checking environment variables...")
    except json.JSONDecodeError:
        print("Error: urls.json is not valid JSON.")

    # Get URLs from environment variable if provided
    env_urls = os.environ.get("STREAMLIT_APP_URL")
    if env_urls:
        # Split by comma and strip whitespace
        from_env = [url.strip() for url in env_urls.split(",") if url.strip()]
        urls.extend(from_env)
    
    # Remove duplicates while preserving order
    unique_urls = []
    for url in urls:
        if url not in unique_urls:
            unique_urls.append(url)
            
    return unique_urls

URLS = load_urls()

def wake_app(driver, url):
    """
    Navigates to the given URL and attempts to click the 'wake-up' button if it exists.
    """
    print(f"\nProcessing: {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        
        try:
            # Look for the wake-up button
            button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes, get this app back up')]"))
            )
            print("  - Wake-up button found. Clicking...")
            button.click()

            # After clicking, check if it disappears
            try:
                wait.until(EC.invisibility_of_element_located((By.XPATH, "//button[contains(text(),'Yes, get this app back up')]")))
                print("  - Button clicked and disappeared ✅ (app should be waking up)")
            except TimeoutException:
                print("  - Button was clicked but did NOT disappear ❌ (possible failure)")
                return False

        except TimeoutException:
            # No button at all → app is assumed to be awake
            print("  - No wake-up button found. Assuming app is already awake ✅")
        
        return True

    except Exception as e:
        print(f"  - Unexpected error for {url}: {e}")
        return False

def main():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    failed_urls = []

    try:
        for url in URLS:
            success = wake_app(driver, url)
            if not success:
                failed_urls.append(url)

    finally:
        driver.quit()
        print("\n" + "="*30)
        print("Script finished.")
        if failed_urls:
            print(f"Failed to wake up the following apps: {failed_urls}")
            exit(1)
        else:
            print("All apps processed successfully.")

if __name__ == "__main__":
    main()