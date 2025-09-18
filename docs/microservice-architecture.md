# Mikroservice Arkitektur Guide - MCP Protocol

## Oversikt

**MCP Travel Weather Server** er bygget med Model Context Protocol (MCP) kompatibel mikroservice-arkitektur. Systemet består av tre HTTP-baserte tjenester med dynamisk tools discovery og intelligent endpoint mapping.

## 🏗️ MCP Arkitekturdiagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                Internet/Users                                   │
└──────────────────────────────┬──────────────────────────────────────────────────┘
                               │ HTTP :8080
┌──────────────────────────────▼──────────────────────────────────────────────────┐
│                          Web Service                                           │
│                       (services/web/)                                          │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   FastAPI App   │  │   Templates     │  │  Static Assets  │                │
│  │   Port 8080     │  │   (HTML/JS)     │  │   (CSS/Images)  │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                  │                                              │
│                                  │ HTTP Proxy                                   │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │ HTTP :8001
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                        Agent Service (MCP Client)                              │
│                      (services/agent/)                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   FastAPI App   │  │   OpenAI GPT-4o │  │ Dynamic Tools   │                │
│  │   Port 8001     │  │   Integration   │  │ Loading & Mapping│               │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│            │                               │                                   │
│            │ Startup Discovery             │ Runtime Calls                     │
│            │ GET /tools                    │ POST|GET|PUT|DELETE               │
└────────────┼───────────────────────────────┼───────────────────────────────────┘
             │                               │ 
             │                               │ HTTP :8000
┌────────────▼───────────────────────────────▼───────────────────────────────────┐
│                     MCP Server (MCP Protocol Compliant)                        │
│                    (services/mcp-server/)                                      │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐
│  │   FastAPI App   │  │  Tools Manifest │  │   Weather API   │  │  HTTP Router│
│  │   Port 8000     │  │  (/tools)       │  │   (OpenWeather) │  │ (GET/POST/  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │ PUT/DELETE) │
│                                                                  └─────────────┘
│                                  │                                              │
│                                  │ External API Calls                          │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                          External APIs                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ OpenWeatherMap  │  │  Nominatim OSM  │  │   Other APIs    │                │
│  │   (Weather)     │  │  (Geocoding)    │  │   (Extensible)  │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## � MCP Protocol Dataflow

```
1. Agent Startup → GET /tools (MCP Discovery)
2. User Request → Agent loads appropriate tool
3. Agent → Intelligent endpoint mapping 
4. MCP Server → Execute tool → External API
5. Response chain back to user
```

## �📦 Tjenestebeskrivelser

### 1. Web Service (`services/web/`)

**Ansvar**: Frontend og brukergrensesnitt
**Port**: 8080
**Teknologi**: FastAPI + Jinja2 Templates + HTTPX

#### Funksjoner:
- HTML/JavaScript grensesnitt for brukerinteraksjon
- Proxy til Agent Service for AI-forespørsler  
- Eksempel spørsmål og interaktiv chat
- Real-time helsestatusindikator
- Responsive design for mobile og desktop

#### API Endpoints:
```
GET  /           - Hovedside (HTML)
POST /query      - Proxy brukerforespørsel til Agent Service
GET  /examples   - Hent foreslåtte eksempel spørsmål
GET  /health     - Helsesjekk med agent tilkobling status
```

#### Dependencies:
- Agent Service (HTTP :8001)

---

### 2. Agent Service (`services/agent/`)

**Ansvar**: AI-orkestrering med MCP Protocol klient
**Port**: 8001  
**Teknologi**: FastAPI + OpenAI GPT-4o + SQLite + HTTPX + MCP Client

#### MCP Features:
- **Dynamisk Tools Discovery**: Laster verktøy fra MCP server ved oppstart
- **Intelligent Endpoint Mapping**: Eksplisitt og konvensjonsbasert routing  
- **HTTP Method Support**: GET, POST, PUT, DELETE routing
- **Tools Caching**: Lagrer tools manifest for performance

#### Funksjoner:
- OpenAI GPT-4o integrasjon med dynamic function calling
- Persistent samtalehistorikk med SQLite database
- MCP protokoll klient for tools discovery
- Intelligent verktøybruk basert på brukerforespørsler
- Kontekstuell respons generering

#### API Endpoints:
```
POST /query      - Prosesser brukerforespørsel med AI
GET  /health     - Helsesjekk med agent readiness status
```

#### Dependencies:
- MCP Server (HTTP :8000)
- OpenAI API (External)

---

### 3. MCP Server (`services/mcp-server/`)

**Ansvar**: MCP Protocol server med tools manifest
**Port**: 8000
**Teknologi**: FastAPI + HTTPX + Eksterne API-er + MCP Protocol

#### MCP Protocol Features:
- **Tools Manifest**: `/tools` endpoint følger MCP spesifikasjon
- **HTTP Method Routing**: GET, POST, PUT, DELETE support
- **Endpoint Metadata**: Eksplisitt endpoint og method informasjon
- **Schema Validation**: JSON schema for alle verktøy

#### Funksjoner:
- Værprognose via OpenWeatherMap API
- Geocoding via Nominatim API
- Server status og ping verktøy
- Robust feilhåndtering og validering

#### API Endpoints:
```
GET  /tools        - MCP tools manifest (følger MCP spec)
POST /weather      - Hent værprognose for lokasjon
POST /ping         - Test tilkobling til server
GET  /status       - Server status informasjon
GET  /health       - Helsesjekk
POST /send-email   - Send reiseinfo på e-post med formatering
GET  /health       - Helsesjekk
```
GET  /health     - Helsesjekk for MCP server
```

#### Dependencies:
- OpenWeatherMap API (External)
- OpenRouteService API (External, Optional)
- Nominatim API (External)

## 🔄 Dataflyt

### Typisk brukerinteraksjon:

1. **Bruker** sender forespørsel via web UI (Port 8080)
2. **Web Service** proxy forespørsel til Agent Service (Port 8001)  
3. **Agent Service** analyserer forespørsel med OpenAI GPT-4o
4. **Agent Service** kaller relevante verktøy på MCP Server (Port 8000)
5. **MCP Server** henter data fra eksterne API-er
6. **Agent Service** kombinerer data og genererer intelligent respons
7. **Web Service** viser respons til bruker i web UI

### Eksempel API kall sekvens:
```
User → Web:8080/query → Agent:8001/query → MCP:8000/weather
                                        → MCP:8000/routes
                      ← OpenAI GPT-4o   ← MCP Server Response
      ← Web Response  ← Agent Response
```

## 🚀 Deployment Konfiguration

### Docker Compose Struktur:
```yaml
services:
  mcp-server:
    build: ./services/mcp-server
    ports: ["8000:8000"]
    environment:
      - OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY}
      - OPENROUTE_API_KEY=${OPENROUTE_API_KEY}
    
  travel-agent:  
    build: ./services/agent
    ports: ["8001:8001"]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MCP_SERVER_URL=http://mcp-server:8000
    depends_on: [mcp-server]
    volumes:
      - agent-data:/data  # Persistent SQLite database
    
  agent-web:
    build: ./services/web  
    ports: ["8080:8080"]
    environment:
      - AGENT_SERVICE_URL=http://travel-agent:8001
    depends_on: [travel-agent]
```

### Helsesjekker:
Alle tjenester har innebygde helsesjekker:
```bash
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Agent Service
curl http://localhost:8080/health  # Web Service
```

## 💡 Fordelene med denne arkitekturen

### Skalerbarhet:
- Hver tjeneste kan skaleres uavhengig
- Load balancing mulig på tjenestenivå
- Horizontal skalering av ressurskrevende komponenter

### Vedlikeholdbarhet:
- Isolerte domener per tjeneste
- Enklere testing og debugging
- Modulær kodebase

### Deployment:
- Rolling updates mulig per tjeneste  
- Isolerte environments
- Container-native design

### Sikkerhet:
- Intern nettverkskommunikasjon
- API-nøkler isolert per tjeneste
- Begrenset eksponering av tjenester

## 🔧 Utviklingsguide

### Lokal utvikling:
```bash
# Start individuell tjeneste for utvikling
cd services/web/
python app.py

# Eller bruk docker-compose for full stack
docker-compose up -d
```

### Logging og monitoring:
```bash
# Se logger for alle tjenester
docker-compose logs -f

# Se logger for spesifikk tjeneste  
docker-compose logs -f travel-agent
```

### Debugging:
```bash
# Koble til container for debugging
docker-compose exec travel-agent bash

# Sjekk nettverk tilkobling
docker-compose exec travel-agent curl http://mcp-server:8000/health
```
