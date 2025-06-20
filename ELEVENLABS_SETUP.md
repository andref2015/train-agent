# ElevenLabs AI Customer Support Integration

This API provides real-time Estonian train departure times for integration with ElevenLabs AI customer support agents.

## API Endpoint

**Base URL**: `https://train-agent-production.up.railway.app`

### Get Train Times
**Endpoint**: `GET /trains`

**Parameters**:
- `from_city` (required): Departure city
- `to_city` (required): Destination city  
- `date` (optional): Date in YYYY-MM-DD format or "tomorrow" (default: "tomorrow")
- `after_time` (optional): Only show trains after this time in HH:MM format (default: "15:00")
- `limit` (optional): Maximum number of results 1-10 (default: 3)

**Supported Cities**: Tallinn, Tartu, Narva, Pärnu, Viljandi

## ElevenLabs Webhook Integration

### Step 1: Create Webhook Tool in ElevenLabs

1. Go to your ElevenLabs dashboard
2. Navigate to "Conversation AI" → "Tools"
3. Click "Create Tool" → "Webhook"
4. Configure as follows:

**Tool Name**: `get_train_times`

**Description**: 
```
Get real-time Estonian train departure and arrival times between cities. Use this when customers ask about train schedules, departure times, or travel between Estonian cities.
```

**Webhook URL**: 
```
https://train-agent-production.up.railway.app/trains
```

**HTTP Method**: `GET`

**Parameters**:

1. **from_city**
   - Type: String
   - Required: Yes
   - Description: "Departure city (Tallinn, Tartu, Narva, Pärnu, or Viljandi)"

2. **to_city**
   - Type: String  
   - Required: Yes
   - Description: "Destination city (Tallinn, Tartu, Narva, Pärnu, or Viljandi)"

3. **date**
   - Type: String
   - Required: No
   - Description: "Date in YYYY-MM-DD format or 'tomorrow' (default: tomorrow)"

4. **after_time**
   - Type: String
   - Required: No
   - Description: "Only show trains after this time in HH:MM format (default: 15:00)"

5. **limit**
   - Type: Integer
   - Required: No
   - Description: "Maximum number of results 1-10 (default: 3)"

### Step 2: Configure AI Agent Prompt

Add this to your AI agent's system prompt:

```
You are a helpful customer support agent for Estonian railway services. When customers ask about train times, departures, or travel between Estonian cities, use the get_train_times tool.

Supported cities: Tallinn, Tartu, Narva, Pärnu, Viljandi

When customers ask about trains:
1. Extract the departure and destination cities
2. Ask for clarification if the date isn't specified (default to "tomorrow")
3. Use the get_train_times tool with appropriate parameters
4. Present the results in a friendly, conversational manner

Example: "I found 3 trains from Tallinn to Tartu tomorrow after 3 PM: The first train departs at 16:27 and arrives at 18:46..."
```

## Example API Responses

### Successful Response
```json
{
  "from_city": "Tallinn",
  "to_city": "Tartu", 
  "date": "2024-12-21",
  "after_time": "15:00",
  "trains": [
    {
      "departure": "16:27",
      "arrival": "18:46", 
      "display": "Depart: 16:27 → Arrive: 18:46"
    },
    {
      "departure": "18:27",
      "arrival": "20:46",
      "display": "Depart: 18:27 → Arrive: 20:46"
    }
  ],
  "execution_time_seconds": 4.2
}
```

### Error Response
```json
{
  "detail": "Unsupported departure city. Supported: ['Tallinn', 'Tartu', 'Narva', 'Pärnu', 'Viljandi']"
}
```

## Testing URLs

Test the API directly with these URLs:

- Basic info: `https://train-agent-production.up.railway.app/`
- Tallinn to Tartu: `https://train-agent-production.up.railway.app/trains?from_city=tallinn&to_city=tartu`
- With date: `https://train-agent-production.up.railway.app/trains?from_city=tallinn&to_city=tartu&date=2024-12-21&after_time=16:00`

## Technical Details

- **Response Time**: ~4-6 seconds (real-time web scraping)
- **Deployment**: Railway.app with Selenium WebDriver
- **Reliability**: Production-ready with error handling
- **CORS**: Enabled for cross-origin requests 
The agent will automatically call the API and provide natural, helpful responses! 🎯 