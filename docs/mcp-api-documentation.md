# API Dokumentasjon - MCP Travel Weather Server

## Oversikt

**MCP Travel Weather Server** tilbyr HTTP-baserte API-er for reiseplanlegging med værdata, implementert som en Model Context Protocol (MCP) kompatibel løsning med dynamisk tools discovery.

### 📚 Relatert Dokumentasjon

- **[Mikroservice Arkitektur Guide](./microservice-architecture.md)** - Detaljert arkitekturguide  
- **[Docker Deployment Guide](./docker-deployment.md)** - Deployment og drift
- **[OpenAPI Schema](./mcp-openapi-schema.md)** - Teknisk API spesifikasjon
- **[MCP Integration Guide](./mcp-integration-guide.md)** - MCP Protocol implementasjon

## 🏗️ API Oversikt

### Tjenestene

| Tjeneste | Port | Ansvar | Dokumentasjon |
|----------|------|---------|---------------|
| **Web Service** | 8080 | Frontend UI & Proxy | [Web API](#web-service-api) |
| **Agent Service** | 8001 | AI Logic & Dynamisk Tools Loading | [Agent API](#agent-service-api) |  
| **MCP Server** | 8000 | MCP Tools Manifest & Endpoints | [MCP API](#mcp-server-api) |

### Base URLs (Docker deployment)
```
Web Service:   http://localhost:8080
Agent Service: http://localhost:8001  
MCP Server:    http://localhost:8000
```

### MCP Protocol Features
- **Dynamisk Tools Discovery**: Agent laster verktøy fra MCP server ved oppstart
- **Tools Manifest**: MCP-kompatibel `/tools` endpoint  
- **Intelligent Endpoint Mapping**: Eksplisitt og konvensjonsbasert routing
- **HTTP Method Support**: GET, POST, PUT, DELETE routing

## 🌐 Web Service API

**Port 8080** - Frontend og brukergrensesnitt

### GET /
Hovedside med web-grensesnitt

**Respons**: HTML side for MCP Travel Weather Server

### POST /query
Proxy brukerforespørsel til Agent Service

**Request Body**:
```json
{
  "query": "Hva er været i Oslo denne uka?"
}
```

**Response**:
```json
{
  "success": true,
  "response": "I Oslo denne uka vil det være...",
  "timestamp": "2025-09-14T21:45:00.000Z",
  "agent_connected": true
}
```

### GET /examples  
Hent foreslåtte eksempel spørsmål

**Response**:
```json
{
  "examples": [
    {
      "title": "🌤️ Værprognose",
      "description": "Få detaljert værmelding for din destinasjon", 
      "query": "Hva er været i Oslo denne uka?"
    }
  ]
}
```

### GET /health
Web service helsesjekk

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-14T21:45:00.000Z",
  "agent_connected": true
}
```

## 🤖 Agent Service API

**Port 8001** - AI-orkestrering med dynamisk tools loading

### Dynamisk Tools Discovery
Agent laster verktøy fra MCP server ved oppstart og mapper endpoints intelligent.

**Features**:
- Automatisk tools discovery via MCP `/tools` manifest
- Eksplisitt endpoint mapping basert på tools metadata
- Konvensjonsbasert fallback mapping
- HTTP method routing (GET, POST, PUT, DELETE)

### POST /query
Prosesser brukerforespørsel med AI og dynamiske verktøy

**Request Body**:
```json
{
  "query": "Planlegg en tur fra Oslo til Bergen med værinfo"
}
```

**Response**:
```json
{
  "success": true,
  "response": "Basert på værprognosen anbefaler jeg...",
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

**Feilrespons**:
```json
{
  "success": false,
  "error": "Beskrivelse av feil",
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

### GET /health
Agent service helsesjekk med tools status

**Response**:
```json
{
  "status": "healthy",
  "service": "MCP Travel Agent",
  "timestamp": "2025-09-14T21:45:00.000Z",
  "agent_ready": true,
  "tools_loaded": 3,
  "mcp_server_connected": true
}
```

## 🛠️ MCP Server API

**Port 8000** - MCP Tools manifest og verktøy implementasjon

### GET /tools
**MCP Tools Manifest** - Eksponerer tilgjengelige verktøy i henhold til MCP spesifikasjon

**Response**:
```json
{
  "tools": [
    {
      "name": "get_weather_forecast",
      "description": "Få værprognose for en gitt destinasjon",
      "inputSchema": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "Navn på sted"}
        },
        "required": ["location"]
      },
      "endpoint": "/weather",
      "method": "POST"
    },
    {
      "name": "ping",
      "description": "Test tilkobling til MCP server",
      "inputSchema": {
        "type": "object", 
        "properties": {
          "message": {"type": "string", "description": "Melding å sende"}
        },
        "required": ["message"]
      },
      "endpoint": "/ping",
      "method": "POST"
    },
    {
      "name": "get_status", 
      "description": "Hent server status informasjon",
      "inputSchema": {"type": "object", "properties": {}},
      "endpoint": "/status",
      "method": "GET"
    }
  ]
}
```

### POST /weather
Hent værprognose for destinasjon

**Request Body**:
```json
{
  "location": "Oslo"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "location": "Oslo, Norge",
    "coordinates": {"lat": 59.9127, "lon": 10.7461},
    "current": {
      "temperature": 15.5,
      "feels_like": 14.2,
      "humidity": 78,
      "description": "delvis skyet",
      "wind_speed": 3.2,
      "timestamp": "2025-09-14T21:45:00.000Z"
    },
    "forecast": [...]
  },
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

### POST /ping
Test tilkobling til MCP server

**Request Body**:
```json
{
  "message": "Hello from agent!"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "message": "Pong! Hello from agent!",
    "timestamp": "2025-09-14T21:45:00.000Z",
    "server_status": "healthy"
  }
}
```

### GET /status
Hent server status informasjon

**Response**:
```json
{
  "success": true,
  "data": {
    "service": "MCP Travel Weather Server",
    "version": "1.0.0", 
    "status": "healthy",
    "uptime_seconds": 12345,
    "tools_available": 3,
    "external_apis": {
      "openweather": "connected",
      "nominatim": "connected"
    },
    "timestamp": "2025-09-14T21:45:00.000Z"
  }
}
```
      "duration_hours": 7.2,
      "instructions": [...]
    }
  },
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

### POST /plan
Lag komplett reiseplan

**Request Body**:
```json
{
  "origin": "Oslo",
  "destination": "Bergen",
  "travel_date": "2025-09-20",
  "mode": "driving",
  "days": 2
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "trip_summary": {...},
    "route": {...},
    "weather": {...},
    "recommendations": [
      "🧥 Pakk varm jakke - det er kaldt",
      "☂️ Ta med paraply - regn i værmeldingen"
    ]
  },
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

### GET /health
MCP server helsesjekk

**Response**:
```json
{
  "status": "healthy",
  "service": "MCP API Server",
  "timestamp": "2025-09-14T21:45:00.000Z"
}
```

### POST /send-email
Send reiseinfo eller annet innhold på e-post

**Request Body**:
```json
{
  "to_email": "user@example.com",
  "subject": "Din reiseplan fra Ingrids Reisetjenester",
  "content": "Her er kjøreruten fra **Oslo til Bergen**:\n\n1. **Start i Oslo** og kjør nordover på **Arbeidergata**.\n2. **Sving til venstre** inn på **Kristian IVs gate**.\n\n**Estimert reisetid:** 8 timer\n**Avstand:** 456 km",
  "content_type": "html"
}
```

**Parameters**:
- `to_email` (string, required): Mottakers e-postadresse
- `subject` (string, required): E-post emne
- `content` (string, required): E-post innhold (støtter markdown formatering)
- `content_type` (string, optional): "text" eller "html" (default: "text")

**Response**:
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "E-post sendt til user@example.com",
    "timestamp": "2025-09-15T18:35:01.541065"
  },
  "timestamp": "2025-09-15T18:35:01.541253"
}
```

**Konfigkrasjon**: Krever SMTP miljøvariabler:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

## 🔧 Brukseksempler

### Komplett brukerforespørsel gjennom systemet

```bash
# 1. Brukerforespørsel til Web Service
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Planlegg tur til Bergen i morgen"}'

# 2. Direkte til Agent Service  
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hva er været i Bergen?"}'

# 3. Direkte verktøybruk på MCP Server
curl -X POST http://localhost:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Bergen"}'
```

### Helsesjekker for alle tjenester

```bash
# Sjekk alle tjenester
curl http://localhost:8080/health && echo
curl http://localhost:8001/health && echo  
curl http://localhost:8000/health && echo
```
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
