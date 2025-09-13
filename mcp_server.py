"""
MCP Travel Weather Server

En Model Context Protocol (MCP) server som kombinerer reisedata med værdata 
for å hjelpe med reiseplanlegging basert på værutsikter på destinasjonen.

Bruker:
- OpenWeatherMap for værdata
- Nominatim (OpenStreetMap) for geocoding  
- OpenRouteService for rute-beregning

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
NOMINATIM_API_BASE = "https://nominatim.openstreetmap.org"
OPENROUTE_API_BASE = "https://api.openrouteservice.org/v2"

# Hent API nøkler fra miljøvariabler
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY")  # Valgfri

if not OPENWEATHER_API_KEY:
    logger.warning("OPENWEATHER_API_KEY ikke satt i miljøvariabler")

# Hjelpefunksjoner for geocoding og ruting
async def geocode_location(location: str) -> tuple[float, float] | None:
    """
    Hent koordinater for et sted ved hjelp av Nominatim (OpenStreetMap).
    
    Args:
        location: Stedsnavn (f.eks. "Oslo, Norway")
    
    Returns:
        Tuple med (latitude, longitude) eller None hvis ikke funnet
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{NOMINATIM_API_BASE}/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            
            headers = {
                "User-Agent": "TravelWeatherAgent/1.0"  # Nominatim krever User-Agent
            }
            
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                result = data[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                logger.info(f"Geocoded {location} to {lat}, {lon}")
                return lat, lon
            else:
                logger.warning(f"Kunne ikke finne koordinater for {location}")
                return None
                
    except Exception as e:
        logger.error(f"Feil ved geocoding av {location}: {e}")
        return None

async def get_route_openroute(origin_coords: tuple[float, float], 
                             destination_coords: tuple[float, float], 
                             profile: str = "driving-car") -> dict | None:
    """
    Hent rute via OpenRouteService.
    
    Args:
        origin_coords: Start koordinater (lat, lon)
        destination_coords: Destinasjon koordinater (lat, lon)
        profile: Profil ("driving-car", "foot-walking", "cycling-regular")
    
    Returns:
        Rute data eller None
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"{OPENROUTE_API_BASE}/directions/{profile}"
            
            # OpenRouteService bruker longitude, latitude (motsatt av Nominatim)
            coordinates = [
                [origin_coords[1], origin_coords[0]],      # origin: [lon, lat]
                [destination_coords[1], destination_coords[0]]  # destination: [lon, lat]
            ]
            
            data = {
                "coordinates": coordinates,
                "format": "json",
                "instructions": True,
                "language": "no"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Legg til API nøkkel hvis tilgjengelig
            if OPENROUTE_API_KEY:
                headers["Authorization"] = OPENROUTE_API_KEY
            
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result
            
    except Exception as e:
        logger.error(f"Feil ved henting av rute via OpenRouteService: {e}")
        return None

async def get_route_fallback(origin: str, destination: str) -> str:
    """
    Fallback rute informasjon når OpenRouteService ikke er tilgjengelig.
    Bruker kun geocoding for å gi grunnleggende informasjon.
    """
    origin_coords = await geocode_location(origin)
    dest_coords = await geocode_location(destination)
    
    if not origin_coords or not dest_coords:
        return f"Kunne ikke finne koordinater for {origin} eller {destination}"
    
    # Beregn luftlinje avstand
    from math import radians, cos, sin, asin, sqrt
    
    def haversine(lon1, lat1, lon2, lat2):
        """Beregn avstand mellom to punkter på jorden."""
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371  # Radius av jorden i km
        return c * r
    
    distance_km = haversine(origin_coords[1], origin_coords[0], 
                           dest_coords[1], dest_coords[0])
    
    # Estimat for reisetid (bil: 80 km/t, gange: 5 km/t)
    driving_time_hours = distance_km / 80
    walking_time_hours = distance_km / 5
    
    return f"""
Reise fra {origin} til {destination}

Koordinater:
• Start: {origin_coords[0]:.4f}, {origin_coords[1]:.4f}
• Destinasjon: {dest_coords[0]:.4f}, {dest_coords[1]:.4f}

Luftlinje avstand: {distance_km:.1f} km

Estimert reisetid:
• Bil: {driving_time_hours:.1f} timer
• Gåing: {walking_time_hours:.1f} timer

Note: Dette er luftlinje beregninger. For nøyaktige ruter, 
bruk dedikerte navigasjonsapper som Google Maps eller OpenStreetMap.
"""


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
    Bruker Nominatim for geocoding og OpenRouteService for ruting.
    
    Args:
        origin: Startpunkt (f.eks. "Oslo, Norway")
        destination: Destinasjon (f.eks. "Bergen, Norway")
        mode: Reisemåte ("driving", "walking", "cycling")
    
    Returns:
        Formatert reiseinformasjon som tekst
    """
    try:
        # Geocod begge steder
        logger.info(f"Henter rute fra {origin} til {destination} ({mode})")
        
        origin_coords = await geocode_location(origin)
        dest_coords = await geocode_location(destination)
        
        if not origin_coords or not dest_coords:
            return await get_route_fallback(origin, destination)
        
        # Map mode til OpenRouteService profiler
        profile_map = {
            "driving": "driving-car",
            "walking": "foot-walking", 
            "cycling": "cycling-regular",
            "bicycling": "cycling-regular"
        }
        
        profile = profile_map.get(mode, "driving-car")
        
        # Prøv OpenRouteService først
        route_data = await get_route_openroute(origin_coords, dest_coords, profile)
        
        if route_data and "routes" in route_data and route_data["routes"]:
            route = route_data["routes"][0]
            summary = route["summary"]
            
            # Konverter fra meter/sekunder til km/timer
            distance_km = summary["distance"] / 1000
            duration_hours = summary["duration"] / 3600
            
            travel_info = f"""
Reise fra {origin} til {destination}

Reisemåte: {mode}
Avstand: {distance_km:.1f} km
Varighet: {duration_hours:.1f} timer

Rute informasjon:
"""
            
            # Legg til detaljerte instruksjoner hvis tilgjengelig
            if "segments" in route:
                for i, segment in enumerate(route["segments"][:5], 1):  # Vis første 5 segmenter
                    if "steps" in segment:
                        for j, step in enumerate(segment["steps"][:3], 1):  # 3 steg per segment
                            if "instruction" in step:
                                instruction = step["instruction"]
                                step_distance = step.get("distance", 0) / 1000
                                travel_info += f"\n{i}.{j}. {instruction} ({step_distance:.1f} km)"
            
            return travel_info
        
        else:
            # Fallback til grunnleggende informasjon
            logger.warning("OpenRouteService ikke tilgjengelig, bruker fallback")
            return await get_route_fallback(origin, destination)
            
    except Exception as e:
        logger.error(f"Feil ved henting av ruter: {e}")
        return f"Feil ved henting av ruter: {str(e)}"


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
