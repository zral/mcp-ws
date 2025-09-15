#!/usr/bin/env python3
"""
MCP API Server

HTTP API wrapper for MCP Travel Weather Server functionality.
Exposes weather, routing, and trip planning as REST endpoints.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP API Server",
    description="HTTP API for travel weather services",
    version="1.0.0"
)

# API konstanter
WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"
NOMINATIM_API_BASE = "https://nominatim.openstreetmap.org"
OPENROUTE_API_BASE = "https://api.openrouteservice.org/v2"

# Hent API nøkler fra miljøvariabler
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY")

if not OPENWEATHER_API_KEY:
    logger.warning("OPENWEATHER_API_KEY ikke satt i miljøvariabler")

# HTTP klient
http_client = httpx.AsyncClient()

# Request/Response modeller
class WeatherRequest(BaseModel):
    location: str

class RouteRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "driving"

class TripRequest(BaseModel):
    origin: str
    destination: str
    travel_date: Optional[str] = None
    mode: str = "driving"
    days: int = 1

class MCPResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str

# Startup/shutdown handlers
@app.on_event("startup")
async def startup_event():
    """Initialiser ved oppstart."""
    logger.info("Starting MCP API Server...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup ved nedstengning."""
    await http_client.aclose()
    logger.info("MCP API Server avsluttet")

# Helper funksjoner
def format_route_instruction(instruction: str) -> str:
    """Formater ruteinstruksjoner ved å legge til markdown bold formatering for viktige ord."""
    import re
    
    # Først håndter eksisterende **tekst** markering (beholdes som den er)
    # Ingen endring nødvendig for eksisterende markdown
    
    # Legg til markdown bold formatering for retninger
    directions = ['Turn left', 'Turn right', 'Keep left', 'Keep right', 'Head north', 
                  'Head south', 'Head east', 'Head west', 'Continue straight',
                  'Enter the roundabout', 'left', 'right', 'straight', 'north', 'south', 'east', 'west']
    
    for direction in directions:
        # Unngå å dobbel-formatere
        pattern = r'\b(?<!\*\*)(' + re.escape(direction) + r')(?!\*\*)\b'
        instruction = re.sub(pattern, r'**\1**', instruction, flags=re.IGNORECASE)
    
    # Legg til markdown bold for veinavnsprisser og viktige steder
    street_patterns = [
        r'\b(?<!\*\*)(\w+(?:gate|vei|veien|gata|gaten|plass|plassen|tunnel|tunnelen))(?!\*\*)\b',
        r'\b(?<!\*\*)(E \d+)(?!\*\*)\b',  # Europavei
        r'\b(?<!\*\*)(\d{3,4})(?!\*\*)\b'  # Fylkesvei nummer
    ]
    
    for pattern in street_patterns:
        instruction = re.sub(pattern, r'**\1**', instruction)
    
    return instruction

async def geocode_location(location: str) -> Optional[Dict[str, float]]:
    """Geocode en lokasjon til koordinater."""
    try:
        params = {
            "q": location,
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }
        
        response = await http_client.get(f"{NOMINATIM_API_BASE}/search", params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
            
        result = data[0]
        return {
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "display_name": result.get("display_name", location)
        }
        
    except Exception as e:
        logger.error(f"Geocoding error for {location}: {e}")
        return None

async def get_weather_forecast(location: str) -> Dict[str, Any]:
    """Hent værprognose for en lokasjon."""
    try:
        # Geocode lokasjonen først
        coords = await geocode_location(location)
        if not coords:
            return {"error": f"Kunne ikke finne koordinater for {location}"}
        
        # Hent værdata
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "no"
        }
        
        # Hent current weather
        current_response = await http_client.get(f"{WEATHER_API_BASE}/weather", params=params)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Hent 5-day forecast
        forecast_response = await http_client.get(f"{WEATHER_API_BASE}/forecast", params=params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        return {
            "location": coords["display_name"],
            "coordinates": {"lat": coords["lat"], "lon": coords["lon"]},
            "current": {
                "temperature": current_data["main"]["temp"],
                "feels_like": current_data["main"]["feels_like"],
                "humidity": current_data["main"]["humidity"],
                "pressure": current_data["main"]["pressure"],
                "description": current_data["weather"][0]["description"],
                "wind_speed": current_data.get("wind", {}).get("speed", 0),
                "timestamp": datetime.fromtimestamp(current_data["dt"]).isoformat()
            },
            "forecast": [
                {
                    "datetime": datetime.fromtimestamp(item["dt"]).isoformat(),
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item.get("wind", {}).get("speed", 0)
                }
                for item in forecast_data["list"][:8]  # Next 24 hours (8 x 3-hour intervals)
            ]
        }
        
    except Exception as e:
        logger.error(f"Weather forecast error: {e}")
        return {"error": f"Kunne ikke hente værprognose: {str(e)}"}

async def get_travel_routes(origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
    """Hent reiseruter mellom to destinasjoner."""
    try:
        # Geocode begge lokasjoner
        origin_coords = await geocode_location(origin)
        dest_coords = await geocode_location(destination)
        
        if not origin_coords or not dest_coords:
            return {"error": "Kunne ikke finne koordinater for en eller begge lokasjoner"}
        
        result = {
            "origin": {"name": origin, "coordinates": origin_coords},
            "destination": {"name": destination, "coordinates": dest_coords},
            "mode": mode
        }
        
        # Prøv OpenRouteService hvis API-nøkkel er tilgjengelig
        if OPENROUTE_API_KEY:
            try:
                profile_map = {
                    "driving": "driving-car",
                    "walking": "foot-walking",
                    "cycling": "cycling-regular"
                }
                profile = profile_map.get(mode, "driving-car")
                
                headers = {"Authorization": OPENROUTE_API_KEY}
                data = {
                    "coordinates": [
                        [origin_coords["lon"], origin_coords["lat"]],
                        [dest_coords["lon"], dest_coords["lat"]]
                    ],
                    "format": "json"
                }
                
                response = await http_client.post(
                    f"{OPENROUTE_API_BASE}/directions/{profile}/json",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    route_data = response.json()
                    route = route_data["routes"][0]
                    
                    result["route"] = {
                        "distance_km": round(route["summary"]["distance"] / 1000, 1),
                        "duration_hours": round(route["summary"]["duration"] / 3600, 1),
                        "instructions": [format_route_instruction(step["instruction"]) for step in route["segments"][0]["steps"]]
                    }
                else:
                    logger.warning(f"OpenRoute API returned status {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"OpenRoute API error: {e}")
        
        # Fallback til luftlinje-avstand
        if "route" not in result:
            # Beregn luftlinje avstand (haversine formel)
            import math
            
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371  # Earth radius in km
                dlat = math.radians(lat2 - lat1)
                dlon = math.radians(lon2 - lon1)
                a = (math.sin(dlat/2)**2 + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                     math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                return R * c
            
            air_distance = haversine_distance(
                origin_coords["lat"], origin_coords["lon"],
                dest_coords["lat"], dest_coords["lon"]
            )
            
            # Estimat reisetidom basert på transportmåte
            speed_map = {"driving": 80, "walking": 5, "cycling": 20}
            avg_speed = speed_map.get(mode, 80)
            estimated_duration = air_distance / avg_speed
            
            result["route"] = {
                "distance_km": round(air_distance * 1.3, 1),  # Add 30% for actual road distance
                "duration_hours": round(estimated_duration * 1.5, 1),  # Add 50% for realistic travel time
                "note": "Estimert basert på luftlinje-avstand",
                "air_distance_km": round(air_distance, 1)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Travel routes error: {e}")
        return {"error": f"Kunne ikke beregne rute: {str(e)}"}

async def plan_trip(origin: str, destination: str, travel_date: Optional[str] = None, 
                   mode: str = "driving", days: int = 1) -> Dict[str, Any]:
    """Lag komplett reiseplan med vær og rute."""
    try:
        # Hent ruteinfo
        route_info = await get_travel_routes(origin, destination, mode)
        if "error" in route_info:
            return route_info
        
        # Hent værinfo for destinasjon
        weather_info = await get_weather_forecast(destination)
        if "error" in weather_info:
            logger.warning(f"Could not get weather for {destination}: {weather_info['error']}")
            weather_info = {"note": "Værdata ikke tilgjengelig"}
        
        # Behandle reisedato
        if travel_date:
            try:
                travel_dt = datetime.fromisoformat(travel_date.replace('Z', '+00:00'))
            except:
                travel_dt = datetime.now()
        else:
            travel_dt = datetime.now()
        
        result = {
            "trip_summary": {
                "origin": route_info["origin"]["name"],
                "destination": route_info["destination"]["name"],
                "travel_date": travel_dt.isoformat(),
                "duration_days": days,
                "transport_mode": mode
            },
            "route": route_info.get("route", {}),
            "weather": weather_info,
            "recommendations": []
        }
        
        # Generer anbefalinger basert på vær og rute
        recommendations = []
        
        if "current" in weather_info:
            temp = weather_info["current"]["temperature"]
            desc = weather_info["current"]["description"]
            
            if temp < 0:
                recommendations.append("🧥 Pakk varme klær - det er under 0°C")
            elif temp < 10:
                recommendations.append("🧥 Pakk varm jakke - det er kaldt")
            elif temp > 25:
                recommendations.append("👕 Lett klær anbefales - det er varmt")
            
            if "regn" in desc.lower() or "rain" in desc.lower():
                recommendations.append("☂️ Ta med paraply - regn i værmeldingen")
            elif "snø" in desc.lower() or "snow" in desc.lower():
                recommendations.append("❄️ Kjør forsiktig - snø i værmeldingen")
        
        if "route" in route_info and "duration_hours" in route_info["route"]:
            duration = route_info["route"]["duration_hours"]
            if duration > 8:
                recommendations.append("🛌 Vurder overnatting underveis - lang reise")
            elif duration > 4:
                recommendations.append("⛽ Planlegg pause underveis")
        
        result["recommendations"] = recommendations
        
        return result
        
    except Exception as e:
        logger.error(f"Trip planning error: {e}")
        return {"error": f"Kunne ikke planlegge reise: {str(e)}"}

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Helse sjekk."""
    return HealthResponse(
        status="healthy",
        service="MCP API Server",
        timestamp=datetime.now().isoformat()
    )

@app.post("/weather", response_model=MCPResponse)
async def get_weather(request: WeatherRequest):
    """Hent værprognose for en destinasjon."""
    try:
        logger.info(f"Weather request for: {request.location}")
        result = await get_weather_forecast(request.location)
        
        return MCPResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/routes", response_model=MCPResponse)
async def get_routes(request: RouteRequest):
    """Hent reiseruter mellom to destinasjoner."""
    try:
        logger.info(f"Route request: {request.origin} -> {request.destination}, mode: {request.mode}")
        result = await get_travel_routes(request.origin, request.destination, request.mode)
        
        return MCPResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Route API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan", response_model=MCPResponse)
async def plan_trip_endpoint(request: TripRequest):
    """Lag komplett reiseplan med vær og rute."""
    try:
        logger.info(f"Trip plan request: {request.origin} -> {request.destination}")
        result = await plan_trip(
            request.origin, 
            request.destination, 
            request.travel_date, 
            request.mode, 
            request.days
        )
        
        return MCPResponse(
            success=True,
            data=result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Trip planning API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting MCP Server API on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
