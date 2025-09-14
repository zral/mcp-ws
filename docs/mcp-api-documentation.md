# MCP Travel Weather Server API Documentation

## Oversikt

Travel Weather MCP Server er en Model Context Protocol (MCP) server som tilbyr værdata og reiseplanlegging. Serveren eksponerer tre hovedfunksjoner som kan brukes av AI-agenter for å hjelpe brukere med reiseplanlegging basert på værforhold.

## Server Informasjon

- **Navn**: Travel Weather MCP Server
- **Versjon**: 1.0.0
- **Protokoll**: Model Context Protocol (MCP)
- **Port**: 8000 (når kjørt standalone)
- **Environment**: Docker container eller direkte Python import

## Tilgjengelige Verktøy (Tools)

### 1. get_weather_forecast

Henter værprognose for en spesifisert lokasjon.

#### Parametere

| Parameter | Type | Påkrevd | Beskrivelse | Standard |
|-----------|------|---------|-------------|----------|
| `location` | string | Ja | Navn på by eller lokasjon (f.eks. "Oslo", "Bergen") | - |
| `days` | integer | Nei | Antall dager fremover å hente prognose for | 5 |

#### Eksempel request
```json
{
  "location": "Oslo",
  "days": 3
}
```

#### Eksempel response
```json
{
  "location": "Oslo",
  "country": "Norway",
  "coordinates": {
    "lat": 59.9133301,
    "lon": 10.7389701
  },
  "forecast": [
    {
      "date": "2025-09-14",
      "day_name": "Saturday",
      "temperature": {
        "min": 8.2,
        "max": 15.4,
        "feels_like": 14.8
      },
      "weather": {
        "main": "Clouds",
        "description": "broken clouds"
      },
      "humidity": 67,
      "wind_speed": 3.2,
      "precipitation": 0
    }
  ],
  "summary": "Delvis skyet vær med temperaturer mellom 8-15°C"
}
```

#### Feilhåndtering
- Returnerer feilmelding hvis lokasjon ikke finnes
- Fallback til engelske stedsnavn hvis norske ikke fungerer
- `days` parameter begrenset til maksimum 5

---

### 2. get_travel_routes

Beregner reiseruter og avstander mellom to lokasjoner.

#### Parametere

| Parameter | Type | Påkrevd | Beskrivelse | Standard |
|-----------|------|---------|-------------|----------|
| `origin` | string | Ja | Startsted (f.eks. "Oslo") | - |
| `destination` | string | Ja | Destinasjon (f.eks. "Bergen") | - |
| `mode` | string | Nei | Transportmiddel: "driving", "walking", "cycling" | "driving" |

#### Eksempel request
```json
{
  "origin": "Oslo",
  "destination": "Bergen",
  "mode": "driving"
}
```

#### Eksempel response
```json
{
  "origin": {
    "name": "Oslo",
    "coordinates": [10.7389701, 59.9133301]
  },
  "destination": {
    "name": "Bergen",
    "coordinates": [5.3259192, 60.3943055]
  },
  "route": {
    "distance_km": 456.0,
    "duration_hours": 8.3,
    "mode": "driving",
    "source": "openroute"
  },
  "travel_advice": {
    "category": "medium_distance",
    "recommendations": [
      "Planlegg for 8-9 timer kjøring",
      "Ta pauser underveis",
      "Sjekk værforhold før avreise"
    ]
  }
}
```

#### Algoritmer

**Primær**: OpenRouteService API
- Nøyaktige vei-avstander
- Realistiske kjøretider  
- Støtter bil, sykkel, gange

**Fallback**: Haversine formel (luftlinje)
- Brukes hvis OpenRouteService feiler
- Estimerte tider basert på transportmiddel
- Mindre nøyaktig, men alltid tilgjengelig

#### Transportmodi

| Mode | Beskrivelse | Hastighet (fallback) |
|------|-------------|---------------------|
| `driving` | Bil/kjøretøy | 60 km/t |
| `walking` | Gange | 5 km/t |
| `cycling` | Sykkel | 15 km/t |

---

### 3. plan_trip

Lager en komplett reiseplan som kombinerer rute og værdata.

#### Parametere

| Parameter | Type | Påkrevd | Beskrivelse | Standard |
|-----------|------|---------|-------------|----------|
| `origin` | string | Ja | Startsted | - |
| `destination` | string | Ja | Destinasjon | - |
| `travel_date` | string | Nei | Reisedato (YYYY-MM-DD format) | I dag |
| `mode` | string | Nei | Transportmiddel | "driving" |
| `days` | integer | Nei | Dager værprognose | 5 |

#### Eksempel request
```json
{
  "origin": "Oslo",
  "destination": "Trondheim", 
  "travel_date": "2025-09-20",
  "mode": "driving",
  "days": 3
}
```

#### Eksempel response
```json
{
  "trip_plan": {
    "route": {
      "distance_km": 497.0,
      "duration_hours": 7.5,
      "mode": "driving"
    },
    "weather": {
      "origin_weather": {
        "location": "Oslo",
        "date": "2025-09-20",
        "temperature": {"min": 10, "max": 18},
        "description": "partly cloudy"
      },
      "destination_weather": {
        "location": "Trondheim", 
        "date": "2025-09-20",
        "temperature": {"min": 8, "max": 15},
        "description": "light rain"
      }
    },
    "recommendations": [
      "Planlegg 7-8 timer kjøring",
      "Regntøy anbefales for Trondheim",
      "Sjekk veimeldinger før avreise"
    ]
  }
}
```

## Tekniske Detaljer

### Avhengigheter

**Eksterne API-er:**
- OpenWeatherMap API (værdata)
- OpenRouteService API (ruteberegning)
- Nominatim/OpenStreetMap (geocoding)

**Python pakker:**
- `httpx` - HTTP klient
- `asyncio` - Asynkron programmering
- `logging` - Logging
- `json` - JSON håndtering
- `os` - Miljøvariabler
- `math` - Matematiske beregninger

### Miljøvariabler

```bash
OPENWEATHER_API_KEY=your_openweather_api_key
OPENROUTE_API_KEY=your_openroute_api_key
```

### Feilhåndtering

**Robuste fallbacks:**
- OpenRouteService → Haversine beregning
- Norske stedsnavn → Engelske stedsnavn
- API rate limits → Retry med exponential backoff

**Loggning:**
- INFO: Normale operasjoner
- WARNING: Fallback-bruk
- ERROR: API-feil og exceptions

### Rate Limiting

- OpenWeatherMap: 60 calls/minute (gratis tier)
- OpenRouteService: 2000 calls/dag (gratis tier)
- Nominatim: 1 call/sekund (fair use)

## Brukseksempler

### Direkte Python import

```python
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip
import asyncio

async def example():
    # Værprognose
    weather = await get_weather_forecast("Oslo", 3)
    print(weather)
    
    # Reiserute
    route = await get_travel_routes("Oslo", "Bergen", "driving")
    print(route)
    
    # Komplett reiseplan
    trip = await plan_trip("Oslo", "Stavanger", "2025-09-20")
    print(trip)

asyncio.run(example())
```

### Via MCP Protocol

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_weather_forecast",
    "arguments": {
      "location": "Bergen",
      "days": 5
    }
  }
}
```

### Docker bruk

```bash
# Start MCP server container
docker run -p 8000:8000 \
  -e OPENWEATHER_API_KEY=your_key \
  -e OPENROUTE_API_KEY=your_key \
  travel-weather-mcp-server

# Test via curl
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_weather_forecast", "arguments": {"location": "Oslo"}}'
```

## Logging og Debugging

Server logger alle operasjoner med timestamps og detaljer:

```
2025-09-14 10:30:15,123 - mcp_server - INFO - Henter værprognose for Oslo (5 dager)
2025-09-14 10:30:15,456 - mcp_server - INFO - Geocoded Oslo to 59.9133301, 10.7389701
2025-09-14 10:30:16,789 - mcp_server - WARNING - OpenRouteService ikke tilgjengelig, bruker fallback
```

## Ytelse

**Typiske responstider:**
- Værprognose: 500-1500ms
- Reiserute (OpenRoute): 200-800ms  
- Reiserute (fallback): 50-200ms
- Komplett reiseplan: 1000-2500ms

**Optimalisering:**
- Parallelle API-kall når mulig
- Caching av geocoding resultater
- Effektive fallback-algoritmer

## Sikkerhet

- API-nøkler via miljøvariabler
- Input validering og sanitering
- Rate limiting respektert
- Ingen sensitive data i logger

## Versjonering

- **v1.0.0**: Initial release med værdata og ruteberegning
- Fremtidige versjoner kan inkludere:
  - Flypriser via offisielle API-er
  - Hotellpriser og bookingdata
  - Historisk værdata
  - Caching og ytelsesoptimalisering
