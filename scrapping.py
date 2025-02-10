import os
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Base URL and main page for the Chamber Finder.
BASE_URL = "https://www.uschamber.com"
MAIN_PAGE = f"{BASE_URL}/co/chambers"

def sanitize_filename(name):
    
    name = name.strip()
    if "\n" in name:
        name = name.split("\n")[0]
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def get_state_links(driver):
    
    state_links = {}
    try:
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "chamber-finder-js"))
        )
        links = container.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            state_name = link.text.strip()
            if href and state_name and ("/co/chambers/" in href) and (href != MAIN_PAGE):
                state_links[state_name] = href
    except Exception as e:
        print("Error while trying to get state links:", e)
    return state_links

def scrape_state(driver, state_name, state_url):
   
    print(f"\nScraping state: {state_name}\nURL: {state_url}")
    driver.get(state_url)
    
  
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".chamber-finder__content"))
        )
    except Exception as e:
        print(f"Timed out waiting for chamber items on {state_name}: {e}")
        return []
    
    
    time.sleep(2)
    
    chambers = []
    try:
       
        chamber_items = driver.find_elements(By.CSS_SELECTOR, ".chamber-finder__content")
        for item in chamber_items:
            try:
                name = item.find_element(By.TAG_NAME, "h3").text.strip()
            except Exception:
                name = "N/A"
            
            try:
                address = item.find_element(By.CSS_SELECTOR, ".chamber-finder__address").text.strip()
            except Exception:
                address = "N/A"
            
            
            website = None
            try:
                links = item.find_elements(By.TAG_NAME, "a")
                for a in links:
                    href = a.get_attribute("href")
                    # If the href is external (does not contain BASE_URL), assume it is the website.
                    if href and href.startswith("http") and BASE_URL not in href:
                        website = href
                        break
            except Exception:
                website = None

            chambers.append({
                "name": name,
                "address": address,
                "website": website
            })
    except Exception as e:
        print(f"Error scraping chambers for {state_name}: {e}")
    return chambers

def save_state_data(state_name, chambers):
    
    safe_state_name = sanitize_filename(state_name)
    output_data = {state_name: chambers}
    filename = f"{safe_state_name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)
    print(f"Saved data for {state_name} in {filename}")

def main():
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    
    driver.get(MAIN_PAGE)
   
    time.sleep(3)
    
    
    state_links = get_state_links(driver)
    if not state_links:
        print("No state links found. Please verify the page structure.")
        driver.quit()
        return
    
    # Create output directory
    output_dir = "chambers_by_state"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)
    
    
    for state_name, state_url in state_links.items():
        chambers = scrape_state(driver, state_name, state_url)
        save_state_data(state_name, chambers)
    
    driver.quit()

if __name__ == "__main__":
    main()