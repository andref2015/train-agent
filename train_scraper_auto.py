#!/usr/bin/env python3
"""
Estonian Railway Train Departure Times Scraper
Optimized for fast performance (~4 seconds)
"""

import sys
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup optimized Chrome driver for speed"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    chrome_options.add_argument('--disable-images')  # Don't load images
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(5)  # Fast timeout
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please make sure you have Chrome browser installed.")
        sys.exit(1)

def extract_departure_arrival_times(text):
    """Extract departure and arrival time pairs"""
    # Look for patterns like "20:2700:04" (departure:arrival)
    departure_arrival_pattern = r'([0-1]?[0-9]|2[0-3]):([0-5][0-9])([0-1]?[0-9]|2[0-3]):([0-5][0-9])'
    matches = re.findall(departure_arrival_pattern, text)
    
    result = []
    for dep_hour, dep_min, arr_hour, arr_min in matches:
        dep_h, dep_m = int(dep_hour), int(dep_min)
        arr_h, arr_m = int(arr_hour), int(arr_min)
        
        # Keep realistic departure times (not 00:xx unless it's after midnight)
        if not (dep_h == 0 and dep_m < 30) and not (dep_h == 1 and dep_m < 10):
            departure_time = f"{dep_hour}:{dep_min}"
            arrival_time = f"{arr_hour}:{arr_min}"
            result.append((departure_time, arrival_time))
    
    return result

def scrape_train_times(url):
    """Fast scraping approach"""
    driver = setup_driver()
    try:
        driver.get(url)
        
        # Quick check for app element
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "app-main")))
        except TimeoutException:
            pass
        
        time.sleep(1.5)  # Minimal but reliable wait
        
        all_text = driver.find_element(By.TAG_NAME, "body").text
        train_times = extract_departure_arrival_times(all_text)
        
        if not train_times:
            # Quick fallback to check specific elements
            try:
                trip_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='trip']")
                for elem in trip_elements[:3]:
                    train_times.extend(extract_departure_arrival_times(elem.text))
            except:
                pass
        
        # Remove duplicates and sort by departure time
        unique_times = []
        seen = set()
        for dep_time, arr_time in train_times:
            if (dep_time, arr_time) not in seen:
                unique_times.append((dep_time, arr_time))
                seen.add((dep_time, arr_time))
        
        try:
            unique_times.sort(key=lambda x: (int(x[0].split(':')[0]), int(x[0].split(':')[1])))
        except:
            pass
            
        return unique_times
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    finally:
        driver.quit()

def main():
    # Start timing from the very beginning
    import time as timer
    script_start_time = timer.time()
    
    # Clear terminal on Mac
    import os
    os.system('clear')
    
    # Get tomorrow's date
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime("%Y-%m-%d")
    
    url = f"https://elron.pilet.ee/en/otsing/Tallinn/Tartu/{date_str}"
    
    print(f"🚂 Tallinn → Tartu Trains ({tomorrow.strftime('%b %d')})")
    
    train_times = scrape_train_times(url)
    
    if train_times:
        # Filter trains after 3PM (15:00) and take first 3
        afternoon_trains = []
        for dep_time, arr_time in train_times:
            dep_hour = int(dep_time.split(':')[0])
            if dep_hour >= 15:  # 3PM or later
                afternoon_trains.append((dep_time, arr_time))
                if len(afternoon_trains) >= 3:  # Only show first 3
                    break
        
        if afternoon_trains:
            print(f"\n{len(afternoon_trains)} trains after 3PM:")
            for i, (dep_time, arr_time) in enumerate(afternoon_trains, 1):
                print(f"{i}. {dep_time} → {arr_time}")
        else:
            print("\nNo trains found after 3PM")
    else:
        print("No trains found")
    
    # End timing at the very end
    script_end_time = timer.time()
    total_execution_time = script_end_time - script_start_time
    
    # Display timing information
    print(f"\n⚡ {total_execution_time:.2f}s")

if __name__ == "__main__":
    main() 