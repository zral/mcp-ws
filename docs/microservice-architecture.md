# Mikroservice Arkitektur Guide

## Oversikt

**Ingrids Reisetjenester** er bygget med en moderne mikroservice-arkitektur bestående av tre HTTP-baserte tjenester. Denne arkitekturen sikrer skalerbarhet, vedlikeholdbarhet og enkel deployment.

## 🏗️ Arkitekturdiagram

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
│                                  │ HTTP Client                                  │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │ HTTP :8001
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                        Agent Service                                           │
│                      (services/agent/)                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   FastAPI App   │  │   OpenAI GPT-4o │  │ Conversation    │                │
│  │   Port 8001     │  │   Integration   │  │ Memory (SQLite) │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                  │                                              │
│                                  │ HTTP Client                                  │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │ HTTP :8000
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                        MCP Server                                              │
│                    (services/mcp-server/)                                      │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  │   FastAPI App   │  │   Weather API   │  │   Route API     │  │   Email SMTP    │
│  │   Port 8000     │  │   (OpenWeather) │  │ (OpenRouteService)│ │   (Gmail/etc)   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
│                                  │                                              │
│                                  │ External API Calls                          │
└──────────────────────────────────┼──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                          External APIs                                         │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ OpenWeatherMap  │  │ OpenRouteService│  │   Nominatim     │                │
│  │   (Weather)     │  │    (Routes)     │  │  (Geocoding)    │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 📦 Tjenestebeskrivelser

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

**Ansvar**: AI-orkestrering og beslutningslogikk
**Port**: 8001  
**Teknologi**: FastAPI + OpenAI GPT-4o + SQLite + HTTPX

#### Funksjoner:
- OpenAI GPT-4o integrasjon med function calling
- Persistent samtalehistorikk med SQLite database
- HTTP klient for MCP Server kommunikasjon
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

**Ansvar**: Verktøy-API for reise- og værdata
**Port**: 8000
**Teknologi**: FastAPI + HTTPX + Eksterne API-er

#### Funksjoner:
- Værprognose via OpenWeatherMap API
- Ruteberegning via OpenRouteService API (med fallback)
- Geocoding via Nominatim API
- Komplett reiseplanlegging med kombinerte data
- **E-post leveranse** med SMTP support og HTML-formatering
- Robust feilhåndtering og fallback algoritmer

#### API Endpoints:
```
POST /weather      - Hent værprognose for lokasjon
POST /routes       - Beregn rute mellom to destinasjoner  
POST /plan         - Lag komplett reiseplan med vær og rute
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
