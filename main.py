import os
import re
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import time

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

def scrape_train_times_simple(from_city: str, to_city: str, date: str, after_time: str = "15:00", limit: int = 3) -> List[Dict[str, Any]]:
    """
    Simplified scraper using requests - may not work if site requires JavaScript
    """
    try:
        # Construct URL
        url = f"https://elron.pilet.ee/en/otsing/{from_city}/{to_city}/{date}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract train times using regex (this is a fallback approach)
        # Looking for patterns like "20:27" followed by another time "22:04"
        time_pattern = r'([0-1]?[0-9]|2[0-3]):([0-5][0-9])'
        times = re.findall(time_pattern, response.text)
        
        # Convert tuples to time strings
        time_strings = [f"{hour.zfill(2)}:{minute}" for hour, minute in times]
        
        # Group times in pairs (departure, arrival)
        train_times = []
        for i in range(0, len(time_strings), 2):
            if i + 1 < len(time_strings):
                departure = time_strings[i]
                arrival = time_strings[i + 1]
                
                # Filter by time
                if is_time_after(departure, after_time):
                    train_times.append({
                        "departure": departure,
                        "arrival": arrival,
                        "display": f"Depart: {departure} → Arrive: {arrival}"
                    })
        
        # Return limited results
        return train_times[:limit]
        
    except Exception as e:
        print(f"Error in simplified scraper: {e}")
        return []

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
    trains = scrape_train_times_simple(from_city_proper, to_city_proper, date, after_time, limit)
    
    execution_time = round(time.time() - start_time, 2)
    
    return {
        "from_city": from_city_proper,
        "to_city": to_city_proper,
        "date": date,
        "after_time": after_time,
        "trains": trains,
        "execution_time_seconds": execution_time,
        "note": "Simplified scraper - may have limited accuracy. For better results, use Selenium version."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 