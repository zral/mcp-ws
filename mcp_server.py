"""
MCP Travel Weather Server

En Model Context Protocol (MCP) server som kombinerer reisedata fra Google 
med værdata for å hjelpe med reiseplanlegging basert på værutsikter på destinasjonen.

Serveren tilbyr følgende verktøy:
- get_travel_routes: Hent ruter og reiseinformasjon mellom to destinasjoner
- get_weather_forecast: Hent værprognose for en destinasjon
- plan_trip: Kombiner reise- og værdata for optimal reiseplanlegging
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent, Tool

# Konfigurer logging til stderr (ikke stdout for MCP)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialiser FastMCP server
mcp = FastMCP("travel-weather-server")

# API konstanter
WEATHER_API_BASE = "https://api.openweathermap.org/data/2.5"
GOOGLE_PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place"
GOOGLE_DIRECTIONS_API_BASE = "https://maps.googleapis.com/maps/api/directions"

# Hent API nøkler fra miljøvariabler
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not OPENWEATHER_API_KEY:
    logger.warning("OPENWEATHER_API_KEY ikke satt i miljøvariabler")
if not GOOGLE_API_KEY:
    logger.warning("GOOGLE_API_KEY ikke satt i miljøvariabler")


@mcp.tool()
async def get_weather_forecast(location: str, days: int = 5) -> str:
    """
    Hent værprognose for en destinasjon.
    
    Args:
        location: Navn på byen eller stedet (f.eks. "Oslo, NO" eller "Paris, France")
        days: Antall dager å hente prognose for (1-5 dager)
    
    Returns:
        Formatert værprognose som tekst
    """
    if not OPENWEATHER_API_KEY:
        return "Feil: OPENWEATHER_API_KEY ikke konfigurert"
    
    try:
        async with httpx.AsyncClient() as client:
            # Først, hent koordinater for lokasjonen
            geocoding_url = "http://api.openweathermap.org/geo/1.0/direct"
            geocoding_params = {
                "q": location,
                "limit": 1,
                "appid": OPENWEATHER_API_KEY
            }
            
            geo_response = await client.get(geocoding_url, params=geocoding_params)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                return f"Fant ikke lokasjon: {location}"
            
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
            
            # Hent værprognose
            forecast_url = f"{WEATHER_API_BASE}/forecast"
            forecast_params = {
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "no"
            }
            
            forecast_response = await client.get(forecast_url, params=forecast_params)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Format værdata
            forecasts = []
            current_date = None
            daily_forecasts = {}
            
            for item in forecast_data["list"][:days * 8]:  # 8 prognoser per dag (hver 3. time)
                dt = datetime.fromtimestamp(item["dt"])
                date_key = dt.strftime("%Y-%m-%d")
                
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "date": dt.strftime("%A, %d. %B %Y"),
                        "temps": [],
                        "weather": item["weather"][0]["description"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"]
                    }
                
                daily_forecasts[date_key]["temps"].append(item["main"]["temp"])
            
            # Lag sammendrag for hver dag
            for date_key, day_data in list(daily_forecasts.items())[:days]:
                min_temp = min(day_data["temps"])
                max_temp = max(day_data["temps"])
                
                forecast = f"""
{day_data["date"]}
Temperatur: {min_temp:.1f}°C - {max_temp:.1f}°C
Vær: {day_data["weather"]}
Luftfuktighet: {day_data["humidity"]}%
Vindstyrke: {day_data["wind_speed"]} m/s
"""
                forecasts.append(forecast.strip())
            
            return f"Værprognose for {location}:\n\n" + "\n---\n".join(forecasts)
            
    except Exception as e:
        logger.error(f"Feil ved henting av værdata: {e}")
        return f"Feil ved henting av værdata: {str(e)}"


@mcp.tool()
async def get_travel_routes(origin: str, destination: str, mode: str = "driving") -> str:
    """
    Hent ruter og reiseinformasjon mellom to destinasjoner.
    
    Args:
        origin: Startpunkt (f.eks. "Oslo, Norway")
        destination: Destinasjon (f.eks. "Bergen, Norway")
        mode: Reisemåte ("driving", "walking", "bicycling", "transit")
    
    Returns:
        Formatert reiseinformasjon som tekst
    """
    if not GOOGLE_API_KEY:
        return "Feil: GOOGLE_API_KEY ikke konfigurert"
    
    try:
        async with httpx.AsyncClient() as client:
            directions_url = f"{GOOGLE_DIRECTIONS_API_BASE}/json"
            directions_params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "language": "no",
                "key": GOOGLE_API_KEY
            }
            
            response = await client.get(directions_url, params=directions_params)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] != "OK":
                return f"Feil ved henting av ruter: {data.get('error_message', data['status'])}"
            
            if not data["routes"]:
                return f"Ingen ruter funnet mellom {origin} og {destination}"
            
            route = data["routes"][0]
            leg = route["legs"][0]
            
            # Format reiseinformasjon
            travel_info = f"""
Reise fra {origin} til {destination}

Reisemåte: {mode}
Avstand: {leg["distance"]["text"]}
Varighet: {leg["duration"]["text"]}

Rute oversikt:
{route["summary"]}

Detaljerte instruksjoner:
"""
            
            for i, step in enumerate(leg["steps"][:10], 1):  # Vis første 10 steg
                instruction = step["html_instructions"].replace("<b>", "").replace("</b>", "").replace("<div>", " ").replace("</div>", "")
                travel_info += f"\n{i}. {instruction} ({step['distance']['text']}, {step['duration']['text']})"
            
            if len(leg["steps"]) > 10:
                travel_info += f"\n... og {len(leg['steps']) - 10} flere steg"
            
            return travel_info
            
    except Exception as e:
        logger.error(f"Feil ved henting av reiseruter: {e}")
        return f"Feil ved henting av reiseruter: {str(e)}"


@mcp.tool()
async def plan_trip(origin: str, destination: str, travel_date: str, mode: str = "driving") -> str:
    """
    Planlegg en reise ved å kombinere reise- og værdata.
    
    Args:
        origin: Startpunkt (f.eks. "Oslo, Norway")
        destination: Destinasjon (f.eks. "Bergen, Norway") 
        travel_date: Reisedato i format YYYY-MM-DD
        mode: Reisemåte ("driving", "walking", "bicycling", "transit")
    
    Returns:
        Komplett reiseplan med vær- og ruteinformasjon
    """
    try:
        # Valider dato format
        try:
            travel_datetime = datetime.strptime(travel_date, "%Y-%m-%d")
        except ValueError:
            return "Feil: Reisedato må være i format YYYY-MM-DD (f.eks. 2024-12-25)"
        
        # Sjekk om datoen er i fremtiden (innenfor 5 dager for værprognose)
        now = datetime.now()
        days_until_travel = (travel_datetime - now).days
        
        if days_until_travel < 0:
            return "Feil: Reisedato kan ikke være i fortiden"
        elif days_until_travel > 5:
            return "Feil: Værprognose er kun tilgjengelig for de neste 5 dagene"
        
        # Hent reiseinformasjon
        logger.info(f"Henter reiseinformasjon fra {origin} til {destination}")
        travel_info = await get_travel_routes(origin, destination, mode)
        
        # Hent værprognose for destinasjonen
        logger.info(f"Henter værprognose for {destination}")
        weather_info = await get_weather_forecast(destination, days=5)
        
        # Kombiner informasjonen til en reiseplan
        trip_plan = f"""
🗓️ REISEPLAN for {travel_date}
{'=' * 50}

📍 RUTE: {origin} → {destination}

{travel_info}

{'=' * 50}

🌤️ VÆRPROGNOSE for destinasjonen:

{weather_info}

{'=' * 50}

💡 REISERÅD:
"""
        
        # Legg til værbaserte råd
        if "regn" in weather_info.lower() or "shower" in weather_info.lower():
            trip_plan += "\n• 🌧️ Ta med regntøy og paraply"
        if "snø" in weather_info.lower() or "snow" in weather_info.lower():
            trip_plan += "\n• ❄️ Sjekk vinterdekkstatus og kjøreforhold"
        if "vind" in weather_info.lower() and mode == "bicycling":
            trip_plan += "\n• 💨 Sterk vind kan påvirke sykling - vurder alternativ transport"
        if mode == "walking" and ("regn" in weather_info.lower() or "snø" in weather_info.lower()):
            trip_plan += "\n• 🚶‍♂️ Værforholdene kan gjøre gåing ubehagelig - vurder alternativ transport"
        
        # Generelle råd
        trip_plan += "\n• 🕐 Sjekk trafikkinformasjon før avreise"
        trip_plan += "\n• 📱 Ha kontaktinformasjon og reservasjoner lett tilgjengelig"
        
        return trip_plan
        
    except Exception as e:
        logger.error(f"Feil ved planlegging av reise: {e}")
        return f"Feil ved planlegging av reise: {str(e)}"


if __name__ == "__main__":
    # Kjør MCP serveren med stdio transport
    logger.info("Starter Travel Weather MCP Server...")
    mcp.run(transport="stdio")
