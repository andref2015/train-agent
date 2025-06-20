# ElevenLabs Setup Guide for Estonian Train Finder API

## 🚀 API Overview

This API transforms the Estonian train scraper into a tool for your ElevenLabs AI customer support agent. It provides real-time train schedules between Estonian cities.

## 📋 API Endpoints

### Main Endpoint: `/trains`
- **Method**: GET
- **Purpose**: Find trains between Estonian cities
- **Perfect for**: AI agents helping customers with travel planning

## ⚙️ ElevenLabs Tool Configuration

### 1. Add Tool in ElevenLabs Dashboard

Go to your Agent settings → Tools → Add Tool → Webhook

**Tool Configuration:**
```
Name: find_estonian_trains
Description: Find train schedules between Estonian cities with departure and arrival times
Method: GET
URL: https://train-voice-agent.vercel.app/trains
```

### 2. Query Parameters Setup

Configure these parameters in ElevenLabs:

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `from_city` | string | Yes | Departure city | "Tallinn" |
| `to_city` | string | Yes | Destination city | "Tartu" |
| `date` | string | Yes | Travel date | "2025-06-21" or "tomorrow" |
| `after_time` | string | No | Show trains after this time | "15:00" |
| `limit` | integer | No | Max trains to return | 3 |

### 3. System Prompt for ElevenLabs Agent

Add this to your agent's system prompt:

```
You are a helpful Estonian travel assistant with access to real-time train schedules. 

When customers ask about trains between Estonian cities, use the find_estonian_trains tool. 

SUPPORTED CITIES: Tallinn, Tartu, Narva, Pärnu, Viljandi

GUIDELINES:
1. Always ask for departure city, destination city, and travel date
2. Default to showing trains after 15:00 (3 PM) unless customer specifies otherwise
3. Present results in a friendly, conversational way
4. If a city is not supported, politely suggest the nearest supported city
5. Use "tomorrow" for next day travel, or YYYY-MM-DD format for specific dates

EXAMPLE RESPONSES:
- "I found 3 trains from Tallinn to Tartu tomorrow after 3 PM. The earliest departs at 15:32 and arrives at 18:19. Would you like to see all options?"
- "For June 21st, there are trains departing at 15:32, 16:52, and 18:11. Which time works best for you?"

Always be helpful and provide clear departure and arrival times.
```

### 4. Example API Calls

The AI agent will make calls like:

```
GET /trains?from_city=Tallinn&to_city=Tartu&date=tomorrow&after_time=15:00&limit=3
```

### 5. API Response Format

The agent receives clean JSON:

```json
{
  "success": true,
  "route": {
    "from": "Tallinn",
    "to": "Tartu", 
    "date": "2025-06-21",
    "date_display": "June 21, 2025"
  },
  "trains": [
    {
      "departure_time": "15:32",
      "arrival_time": "18:19",
      "duration_display": "15:32 → 18:19"
    }
  ],
  "summary": {
    "total_found": 3,
    "message": "Found 3 trains from Tallinn to Tartu after 15:00"
  },
  "execution_time_seconds": 4.41
}
```

## 🏃‍♂️ Quick Test

Test your API with:
```bash
curl "https://train-voice-agent.vercel.app/trains?from_city=Tallinn&to_city=Tartu&date=tomorrow&after_time=15:00&limit=3"
```

## 🚀 Deployment to Vercel

1. Push your code to GitHub
2. Connect GitHub repo to Vercel
3. Deploy automatically
4. Use the Vercel URL in ElevenLabs tool configuration

## 📞 Customer Support Use Cases

Your AI agent can now handle:
- "I need a train from Tallinn to Tartu tomorrow afternoon"
- "What trains are available from Narva to Tallinn after 3 PM?"
- "Show me morning trains from Pärnu to Tallinn on June 25th"

The agent will automatically call the API and provide natural, helpful responses! 🎯 