import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

app = FastAPI(title="Estonian Train Times API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported Estonian cities
SUPPORTED_CITIES = {
    "tallinn": "Tallinn",
    "tartu": "Tartu", 
    "narva": "Narva",
    "pärnu": "Pärnu",
    "viljandi": "Viljandi"
}

def get_tomorrow_date():
    """Get tomorrow's date in YYYY-MM-DD format"""
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d")

def parse_time(time_str: str) -> tuple:
    """Parse time string to hour and minute for comparison"""
    try:
        hour, minute = map(int, time_str.split(':'))
        return hour, minute
    except:
        return 0, 0

def is_time_after(time_str: str, after_time: str) -> bool:
    """Check if time_str is after after_time"""
    time_hour, time_min = parse_time(time_str)
    after_hour, after_min = parse_time(after_time)
    
    time_minutes = time_hour * 60 + time_min
    after_minutes = after_hour * 60 + after_min
    
    return time_minutes >= after_minutes

def create_driver():
    """Create and configure Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # For Railway deployment
    chrome_binary_path = os.environ.get("CHROME_BIN")
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        return None

def scrape_train_times(from_city: str, to_city: str, date: str, after_time: str = "15:00", limit: int = 3) -> List[Dict[str, Any]]:
    """Scrape train times using Selenium"""
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return []
        
        # Navigate to the URL
        url = f"https://elron.pilet.ee/en/otsing/{from_city}/{to_city}/{date}"
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get page source and extract times with regex
        page_source = driver.page_source
        
        # Pattern to match times like "20:27" followed by another time "22:04"
        time_pattern = r'([0-1]?[0-9]|2[0-3]):([0-5][0-9])([0-1]?[0-9]|2[0-3]):([0-5][0-9])'
        matches = re.findall(time_pattern, page_source)
        
        train_times = []
        for match in matches:
            departure = f"{match[0].zfill(2)}:{match[1]}"
            arrival = f"{match[2].zfill(2)}:{match[3]}"
            
            # Filter by time
            if is_time_after(departure, after_time):
                train_times.append({
                    "departure": departure,
                    "arrival": arrival,
                    "display": f"Depart: {departure} → Arrive: {arrival}"
                })
        
        # Remove duplicates and limit results
        seen = set()
        unique_trains = []
        for train in train_times:
            train_key = f"{train['departure']}-{train['arrival']}"
            if train_key not in seen:
                seen.add(train_key)
                unique_trains.append(train)
        
        return unique_trains[:limit]
        
    except Exception as e:
        print(f"Error scraping train times: {e}")
        return []
    finally:
        if driver:
            driver.quit()

@app.get("/")
async def root():
    return {
        "message": "Estonian Train Times API",
        "endpoints": {
            "/trains": "Get train departure times",
        },
        "supported_cities": list(SUPPORTED_CITIES.values())
    }

@app.get("/trains")
async def get_trains(
    from_city: str = Query(..., description="Departure city"),
    to_city: str = Query(..., description="Destination city"), 
    date: str = Query("tomorrow", description="Date in YYYY-MM-DD format or 'tomorrow'"),
    after_time: str = Query("15:00", description="Only show trains after this time (HH:MM)"),
    limit: int = Query(3, description="Maximum number of results", ge=1, le=10)
):
    """Get train times between Estonian cities"""
    
    start_time = time.time()
    
    # Normalize city names
    from_city = from_city.lower().strip()
    to_city = to_city.lower().strip()
    
    # Validate cities
    if from_city not in SUPPORTED_CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported departure city. Supported: {list(SUPPORTED_CITIES.values())}")
    
    if to_city not in SUPPORTED_CITIES:
        raise HTTPException(status_code=400, detail=f"Unsupported destination city. Supported: {list(SUPPORTED_CITIES.values())}")
    
    # Handle date
    if date.lower() == "tomorrow":
        date = get_tomorrow_date()
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format or 'tomorrow'")
    
    # Get proper city names
    from_city_proper = SUPPORTED_CITIES[from_city]
    to_city_proper = SUPPORTED_CITIES[to_city]
    
    # Scrape train times
    trains = scrape_train_times(from_city_proper, to_city_proper, date, after_time, limit)
    
    execution_time = round(time.time() - start_time, 2)
    
    return {
        "from_city": from_city_proper,
        "to_city": to_city_proper,
        "date": date,
        "after_time": after_time,
        "trains": trains,
        "execution_time_seconds": execution_time
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 