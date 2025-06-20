from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import re
import requests
from typing import Optional

app = FastAPI(
    title="Estonian Train Finder API",
    description="Find train schedules between Estonian cities for AI customer support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estonian cities mapping
ESTONIAN_CITIES = {
    "tallinn": "Tallinn",
    "tartu": "Tartu", 
    "narva": "Narva",
    "pärnu": "Pärnu",
    "viljandi": "Viljandi"
}

def extract_departure_arrival_times(text):
    """Extract departure and arrival time pairs"""
    departure_arrival_pattern = r'([0-1]?[0-9]|2[0-3]):([0-5][0-9])([0-1]?[0-9]|2[0-3]):([0-5][0-9])'
    matches = re.findall(departure_arrival_pattern, text)
    
    result = []
    for dep_hour, dep_min, arr_hour, arr_min in matches:
        dep_h, dep_m = int(dep_hour), int(dep_min)
        arr_h, arr_m = int(arr_hour), int(arr_min)
        
        # Keep realistic departure times
        if not (dep_h == 0 and dep_m < 30) and not (dep_h == 1 and dep_m < 10):
            departure_time = f"{dep_hour}:{dep_min}"
            arrival_time = f"{arr_hour}:{arr_min}"
            result.append((departure_time, arrival_time))
    
    return result

def scrape_train_times_simple(from_city: str, to_city: str, date_str: str):
    """Simple scraping approach using requests (may be less reliable)"""
    url = f"https://elron.pilet.ee/en/otsing/{from_city}/{to_city}/{date_str}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Extract times from HTML content
        train_times = extract_departure_arrival_times(response.text)
        
        # Remove duplicates and sort
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch train data: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Estonian Train Finder API - Use /trains endpoint"}

@app.get("/trains")
async def get_trains(
    from_city: str = Query(..., description="Departure city (e.g., Tallinn, Tartu, Narva)"),
    to_city: str = Query(..., description="Destination city (e.g., Tallinn, Tartu, Narva)"), 
    date: str = Query(..., description="Travel date in YYYY-MM-DD format or 'tomorrow'"),
    after_time: Optional[str] = Query("15:00", description="Show trains departing after this time (HH:MM format)"),
    limit: Optional[int] = Query(3, description="Maximum number of trains to return")
):
    """
    Find trains between Estonian cities with time filtering.
    
    Simplified version for Vercel deployment (may be less reliable than Selenium version).
    """
    
    # Normalize city names
    from_city_norm = from_city.lower().strip()
    to_city_norm = to_city.lower().strip()
    
    # Validate cities
    if from_city_norm not in ESTONIAN_CITIES:
        available_cities = ", ".join(ESTONIAN_CITIES.values())
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown departure city '{from_city}'. Available cities: {available_cities}"
        )
    
    if to_city_norm not in ESTONIAN_CITIES:
        available_cities = ", ".join(ESTONIAN_CITIES.values())
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown destination city '{to_city}'. Available cities: {available_cities}"
        )
    
    if from_city_norm == to_city_norm:
        raise HTTPException(status_code=400, detail="Departure and destination cities cannot be the same")
    
    # Handle date parsing
    if date.lower() == "tomorrow":
        travel_date = datetime.now() + timedelta(days=1)
        date_str = travel_date.strftime("%Y-%m-%d")
    else:
        try:
            travel_date = datetime.strptime(date, "%Y-%m-%d")
            date_str = date
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid date format. Use YYYY-MM-DD or 'tomorrow'"
            )
    
    # Parse after_time
    try:
        after_hour, after_min = map(int, after_time.split(':'))
        if not (0 <= after_hour <= 23 and 0 <= after_min <= 59):
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid time format. Use HH:MM (e.g., 15:00)"
        )
    
    # Get proper city names for URL
    from_city_proper = ESTONIAN_CITIES[from_city_norm]
    to_city_proper = ESTONIAN_CITIES[to_city_norm]
    
    # Scrape train times
    import time
    start_time = time.time()
    all_trains = scrape_train_times_simple(from_city_proper, to_city_proper, date_str)
    execution_time = time.time() - start_time
    
    # Filter trains after specified time
    filtered_trains = []
    for dep_time, arr_time in all_trains:
        dep_hour, dep_min = map(int, dep_time.split(':'))
        if dep_hour > after_hour or (dep_hour == after_hour and dep_min >= after_min):
            filtered_trains.append({
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "duration_display": f"{dep_time} → {arr_time}"
            })
            if len(filtered_trains) >= limit:
                break
    
    return {
        "success": True,
        "route": {
            "from": from_city_proper,
            "to": to_city_proper,
            "date": date_str,
            "date_display": travel_date.strftime("%B %d, %Y")
        },
        "filters": {
            "after_time": after_time,
            "limit": limit
        },
        "trains": filtered_trains,
        "summary": {
            "total_found": len(filtered_trains),
            "message": f"Found {len(filtered_trains)} trains from {from_city_proper} to {to_city_proper} after {after_time}"
        },
        "execution_time_seconds": round(execution_time, 2),
        "note": "Simplified version - may be less reliable than Selenium-based scraping"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 