# MCP Server Integration Guide

## Oversikt

Denne guiden viser hvordan du integrerer med MCP Travel Weather Server som følger Model Context Protocol (MCP) spesifikasjon med dynamisk tools discovery.

> **📋 For detaljert arkitektur og template for å lage egne MCP agenter, se [MCP Arkitektur & Template Guide](./mcp-architecture-template.md)**

## MCP Protocol Features

### Dynamisk Tools Discovery
MCP serveren eksponerer tilgjengelige verktøy via `/tools` endpoint i henhold til MCP spesifikasjon:

```python
import requests

# Hent tools manifest fra MCP server
def load_tools_from_mcp():
    response = requests.get("http://localhost:8000/tools")
    tools_data = response.json()
    return tools_data["tools"]

# Eksempel output
tools = load_tools_from_mcp()
print(f"Tilgjengelige verktøy: {len(tools)}")
for tool in tools:
    print(f"- {tool['name']}: {tool['description']} ({tool['method']} {tool['endpoint']})")
```

### OpenAI Function Calling Integration

```python
import openai
import requests

class MCPTravelAgent:
    def __init__(self, openai_api_key, mcp_server_url="http://localhost:8000"):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.mcp_server_url = mcp_server_url
        self.tools = []
        self.tool_endpoints = {}
        
        # Last verktøy dynamisk fra MCP server
        self.load_tools_from_mcp()
        
    def load_tools_from_mcp(self):
        """Last verktøy fra MCP server og konverter til OpenAI format"""
        try:
            response = requests.get(f"{self.mcp_server_url}/tools")
            tools_data = response.json()
            
            for tool in tools_data["tools"]:
                # Lagre endpoint mapping
                self.tool_endpoints[tool["name"]] = {
                    "endpoint": tool["endpoint"], 
                    "method": tool["method"]
                }
                
                # Konverter til OpenAI function format
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["inputSchema"]
                    }
                }
                self.tools.append(openai_tool)
                
            print(f"Lastet {len(self.tools)} verktøy fra MCP server")
            
        except Exception as e:
            print(f"Kunne ikke laste verktøy fra MCP server: {e}")
            
    def call_mcp_tool(self, tool_name, parameters):
        """Kall MCP verktøy via HTTP"""
        if tool_name not in self.tool_endpoints:
            raise ValueError(f"Ukjent verktøy: {tool_name}")
            
        endpoint_info = self.tool_endpoints[tool_name] 
        url = f"{self.mcp_server_url}{endpoint_info['endpoint']}"
        method = endpoint_info["method"]
        
        try:
            if method == "GET":
                response = requests.get(url, params=parameters)
            elif method == "POST":
                response = requests.post(url, json=parameters)
            elif method == "PUT":
                response = requests.put(url, json=parameters)
            elif method == "DELETE":
                response = requests.delete(url, json=parameters)
            else:
                raise ValueError(f"Ukjent HTTP method: {method}")
                
            return response.json()
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    async def process_query(self, user_query):
        """Prosesser brukerforespørsel med AI og dynamiske verktøy"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Du er en reiseassistent som hjelper med værdata."},
                    {"role": "user", "content": user_query}
                ],
                tools=self.tools,  # Dynamisk lastet fra MCP server
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Sjekk om AI ønsker å bruke verktøy
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Kall MCP verktøy via HTTP
                    result = self.call_mcp_tool(function_name, arguments)
                    print(f"Verktøy {function_name} returnerte: {result}")
                    
            return message.content
            
        except Exception as e:
            return f"Feil ved prosessering: {e}"

# Eksempel bruk
async def main():
    agent = MCPTravelAgent(openai_api_key="your_key_here")
    
    # Test dynamisk tools loading
    response = await agent.process_query("Hva er været i Oslo?")
    print(response)

# Kjør eksempel
asyncio.run(main())
```

## Direkte HTTP API Integrasjon

### Test MCP Tools Manifest

```python
import requests

def test_mcp_server():
    base_url = "http://localhost:8000"
    
    # Hent tools manifest
    print("=== MCP Tools Manifest ===")
    response = requests.get(f"{base_url}/tools")
    tools = response.json()["tools"]
    
    for tool in tools:
        print(f"Verktøy: {tool['name']}")
        print(f"  Beskrivelse: {tool['description']}")
        print(f"  Endpoint: {tool['method']} {tool['endpoint']}")
        print(f"  Schema: {tool['inputSchema']}")
        print()
    
    # Test alle verktøy
    print("=== Test Alle Verktøy ===")
    
    # Test weather verktøy
    weather_response = requests.post(f"{base_url}/weather", 
        json={"location": "Oslo"})
    print(f"Weather: {weather_response.json()}")
    
    # Test ping verktøy  
    ping_response = requests.post(f"{base_url}/ping",
        json={"message": "Hello MCP!"})
    print(f"Ping: {ping_response.json()}")
    
    # Test status verktøy
    status_response = requests.get(f"{base_url}/status")
    print(f"Status: {status_response.json()}")

if __name__ == "__main__":
    test_mcp_server()
```
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Utfør MCP verktøykall"""
        if tool_name == "get_weather_forecast":
            return await get_weather_forecast(**arguments)
        elif tool_name == "get_travel_routes":
            return await get_travel_routes(**arguments)
        elif tool_name == "plan_trip":
            return await plan_trip(**arguments)
        else:
            raise ValueError(f"Ukjent verktøy: {tool_name}")
    
    async def process_query(self, query: str):
        """Prosesser brukerforespørsel med AI og verktøy"""
        messages = [
            {
                "role": "system",
                "content": "Du er en reiseplanleggingsassistent. Bruk tilgjengelige verktøy for å hjelpe brukere."
            },
            {
                "role": "user", 
                "content": query
            }
        ]
        
        # Første API-kall til OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Sjekk om AI vil bruke verktøy
        if response_message.tool_calls:
            # Utfør verktøykall
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Kall MCP verktøy
                tool_result = await self.call_tool(function_name, arguments)
                
                # Legg til verktøyresultat i samtale
                messages.append(response_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })
            
            # Få endelig svar fra AI
            final_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            return final_response.choices[0].message.content
        else:
            return response_message.content

# Bruk agenten
agent = TravelWeatherAgent("your_openai_api_key")
result = asyncio.run(agent.process_query("Hvordan er været i Bergen?"))
print(result)
```

## FastAPI Web Integration

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip
import asyncio

app = FastAPI(title="Travel Weather API")

class WeatherRequest(BaseModel):
    location: str
    days: int = 5

class RouteRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "driving"

class TripRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str = None
    mode: str = "driving"
    days: int = 5

@app.post("/weather")
async def get_weather(request: WeatherRequest):
    try:
        result = await get_weather_forecast(request.location, request.days)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/route")
async def get_route(request: RouteRequest):
    try:
        result = await get_travel_routes(request.origin, request.destination, request.mode)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/trip")
async def plan_trip_endpoint(request: TripRequest):
    try:
        result = await plan_trip(
            request.origin, 
            request.destination,
            request.travel_date,
            request.mode,
            request.days
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Docker Integration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY mcp_server.py .
COPY your_app.py .

ENV OPENWEATHER_API_KEY=your_key
ENV OPENROUTE_API_KEY=your_key

CMD ["python", "your_app.py"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  travel-weather-app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY}
      - OPENROUTE_API_KEY=${OPENROUTE_API_KEY}
    restart: unless-stopped
```

## Testing

### Unit Tests
```python
import pytest
import asyncio
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip

@pytest.mark.asyncio
async def test_weather_forecast():
    result = await get_weather_forecast("Oslo", 1)
    assert result is not None
    assert "location" in result
    assert result["location"] == "Oslo"

@pytest.mark.asyncio 
async def test_travel_routes():
    result = await get_travel_routes("Oslo", "Bergen", "driving")
    assert result is not None
    assert "route" in result
    assert result["route"]["distance_km"] > 0

@pytest.mark.asyncio
async def test_plan_trip():
    result = await plan_trip("Oslo", "Stavanger")
    assert result is not None
    assert "trip_plan" in result

# Kjør tester
# pytest test_mcp_server.py -v
```

### Load Testing
```python
import asyncio
import time
from mcp_server import get_weather_forecast

async def load_test():
    start_time = time.time()
    
    # Kjør 100 parallelle forespørsler
    tasks = []
    for i in range(100):
        task = get_weather_forecast("Oslo", 1)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    duration = end_time - start_time
    
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    error_count = len(results) - success_count
    
    print(f"Load test results:")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Successful requests: {success_count}")
    print(f"Failed requests: {error_count}")
    print(f"Requests per second: {len(results)/duration:.2f}")

asyncio.run(load_test())
```

## Error Handling Best Practices

```python
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

async def safe_weather_call(location: str, days: int = 5) -> Optional[Dict[str, Any]]:
    """Sikker wrapper for værprognose med error handling"""
    try:
        result = await get_weather_forecast(location, days)
        return result
    except Exception as e:
        logger.error(f"Feil ved henting av værdata for {location}: {e}")
        return None

async def safe_route_call(origin: str, destination: str, mode: str = "driving") -> Optional[Dict[str, Any]]:
    """Sikker wrapper for ruteberegning"""
    try:
        result = await get_travel_routes(origin, destination, mode)
        return result
    except Exception as e:
        logger.error(f"Feil ved ruteberegning {origin}->{destination}: {e}")
        return None

# Bruk med graceful degradation
async def robust_trip_planning(origin: str, destination: str):
    """Robust reiseplanlegging med fallbacks"""
    
    # Prøv først komplett reiseplan
    try:
        trip = await plan_trip(origin, destination)
        return trip
    except Exception as e:
        logger.warning(f"Komplett reiseplan feilet: {e}")
    
    # Fallback: separat henting av data
    weather_task = safe_weather_call(destination)
    route_task = safe_route_call(origin, destination)
    
    weather, route = await asyncio.gather(weather_task, route_task)
    
    # Bygg delvis resultat
    partial_result = {
        "origin": origin,
        "destination": destination,
        "weather": weather if weather else "Værdata ikke tilgjengelig",
        "route": route if route else "Rutedata ikke tilgjengelig"
    }
    
    return partial_result
```

## Performance Tips

1. **Parallelle kall**: Bruk `asyncio.gather()` for samtidig API-forespørsler
2. **Caching**: Implementer caching for ofte brukte lokasjoner  
3. **Rate limiting**: Respekter API rate limits
4. **Timeout**: Sett reasonable timeouts på HTTP requests
5. **Connection pooling**: Bruk `httpx.AsyncClient()` for connection reuse

## Monitoring og Logging

```python
import logging
import time
from functools import wraps

def monitor_performance(func):
    """Decorator for ytelsesovervåking"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Bruk på MCP funksjoner
@monitor_performance
async def monitored_weather_forecast(location: str, days: int = 5):
    return await get_weather_forecast(location, days)
```
