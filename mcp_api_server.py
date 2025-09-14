#!/usr/bin/env python3
"""
MCP Server as HTTP API

Kjører MCP funksjoner som en HTTP API server for mikrotjeneste arkitektur.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import MCP funksjoner
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP Server API",
    description="HTTP API for MCP verktøyfunksjoner - værdata, ruter og reiseplanlegging",
    version="1.0.0"
)

# Request modeller
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

class MCPResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    timestamp: str

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MCP Server API",
        "timestamp": datetime.now().isoformat()
    }

# MCP Endpoints
@app.post("/weather", response_model=MCPResponse)
async def get_weather(request: WeatherRequest):
    """Hent værprognose for en destinasjon."""
    try:
        logger.info(f"Weather request: {request.location}, {request.days} days")
        result = await get_weather_forecast(request.location, request.days)
        
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
