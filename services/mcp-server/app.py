#!/usr/bin/env python3
"""
MCP API Server - LAB01 VERSION

Forenklet HTTP API med kun værfunksjonalitet for workshop.
Deltagerne kan utvide denne med egne tools.
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
    title="MCP API Server - Lab01",
    description="Forenklet HTTP API for workshop med kun værfunksjonalitet",
    version="1.0.0"
)

# API konstanter
WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"
NOMINATIM_API_BASE = "https://nominatim.openstreetmap.org"

# Hent API nøkler fra miljøvariabler
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not OPENWEATHER_API_KEY:
    logger.warning("OPENWEATHER_API_KEY ikke satt i miljøvariabler")

# HTTP klient
http_client = httpx.AsyncClient()

# Request/Response modeller
class WeatherRequest(BaseModel):
    location: str

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
    logger.info("Starting MCP API Server Lab01...")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup ved nedstengning."""
    await http_client.aclose()
    logger.info("MCP API Server Lab01 avsluttet")

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
            "lon": float(result["lon"])
        }
        
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None

async def get_weather_forecast(location: str) -> Dict[str, Any]:
    """Hent værprognose for en destinasjon."""
    try:
        if not OPENWEATHER_API_KEY:
            return {"error": "OpenWeather API-nøkkel mangler"}
        
        # Geocode lokasjon
        coords = await geocode_location(location)
        if not coords:
            return {"error": f"Kunne ikke finne lokasjon: {location}"}
        
        # Hent nåværende vær
        current_params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "no"
        }
        
        current_response = await http_client.get(f"{WEATHER_API_BASE}/weather", params=current_params)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Hent 5-dagers prognose
        forecast_response = await http_client.get(f"{WEATHER_API_BASE}/forecast", params=current_params)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        
        # Formater resultat
        result = {
            "location": {
                "name": location,
                "coordinates": [coords["lat"], coords["lon"]]
            },
            "current": {
                "temperature": round(current_data["main"]["temp"]),
                "feels_like": round(current_data["main"]["feels_like"]),
                "humidity": current_data["main"]["humidity"],
                "description": current_data["weather"][0]["description"],
                "wind_speed": current_data["wind"]["speed"],
                "timestamp": datetime.now().isoformat()
            },
            "forecast": []
        }
        
        # Prosesser 5-dagers prognose (gruppér etter dag)
        daily_forecasts = {}
        for item in forecast_data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.strftime("%Y-%m-%d")
            
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = {
                    "date": date_key,
                    "temp_min": item["main"]["temp"],
                    "temp_max": item["main"]["temp"],
                    "descriptions": [],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"]
                }
            
            daily_forecasts[date_key]["temp_min"] = min(daily_forecasts[date_key]["temp_min"], item["main"]["temp"])
            daily_forecasts[date_key]["temp_max"] = max(daily_forecasts[date_key]["temp_max"], item["main"]["temp"])
            daily_forecasts[date_key]["descriptions"].append(item["weather"][0]["description"])
        
        # Formater dagsprognose
        for date_key in sorted(daily_forecasts.keys())[:5]:
            day = daily_forecasts[date_key]
            result["forecast"].append({
                "date": day["date"],
                "temp_min": round(day["temp_min"]),
                "temp_max": round(day["temp_max"]),
                "description": max(set(day["descriptions"]), key=day["descriptions"].count),
                "humidity": day["humidity"],
                "wind_speed": day["wind_speed"]
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Weather forecast error: {e}")
        return {"error": f"Kunne ikke hente væropplysninger: {str(e)}"}

# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Helse sjekk."""
    return HealthResponse(
        status="healthy",
        service="MCP API Server Lab01",
        timestamp=datetime.now().isoformat()
    )

@app.get("/tools")
async def list_tools():
    """
    List available tools according to MCP specification.
    Returns tools in MCP-compatible format.
    https://modelcontextprotocol.io/specification/2025-06-18/server/tools
    """
    tools = [
        {
            "name": "get_weather_forecast",
            "description": "Hent værprognose for en destinasjon",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Navn på by eller lokasjon"
                    }
                },
                "required": ["location"]
            },
            "endpoint": "/weather",
            "method": "POST"
        },
        {
            "name": "get_ping",
            "description": "Test verktøy som returnerer en enkel ping respons",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Melding som skal echoes tilbake",
                        "default": "ping"
                    }
                }
            },
            "endpoint": "/ping",
            "method": "POST"
        },
        {
            "name": "get_server_status",
            "description": "Hent status informasjon om MCP serveren",
            "inputSchema": {
                "type": "object",
                "properties": {}
            },
            "endpoint": "/status",
            "method": "GET"
        }
    ]
    
    return {
        "tools": tools
    }

class PingRequest(BaseModel):
    message: str = "ping"

@app.get("/status")
async def get_server_status():
    """Hent status informasjon om MCP serveren."""
    return {
        "success": True,
        "data": {
            "server": "MCP API Server Lab01",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "available_tools": len([tool for tool in [
                {"name": "get_weather_forecast"},
                {"name": "get_ping"},
                {"name": "get_server_status"}
            ]])
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/ping", response_model=MCPResponse)
async def ping(request: PingRequest):
    """Test endpoint som returnerer en enkel ping respons."""
    return MCPResponse(
        success=True,
        data={"message": f"pong: {request.message}", "timestamp": datetime.now().isoformat()},
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

if __name__ == "__main__":
    logger.info("Starting MCP Server API Lab01 on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)