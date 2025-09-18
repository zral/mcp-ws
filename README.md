# MCP Travel Weather Server - LAB01

## Dokumentasjon

**[Workshop Guide](./WORKSHOP.md)** - Komplett workshop dokumentasjon  
**[Presentasjon](./workshop-presentation.html)** - Norsk workshop presentasjon

### Workshop ressurser:
- **[Workshop Guide](./WORKSHOP.md)** - Detaljert lab guide for workshop deltagere
- **[Presentasjon](./workshop-presentation.html)** - Slide deck for workshop
- **[PowerPoint](./workshop-presentation.pptx)** - PowerPoint versjon av presentasjon

## Oversikt

**MCP Travel Weather Server** er en forenklet implementasjon for workshop LAB01. Dette er en **læringsorientert versjon** som demonstrerer Model Context Protocol (MCP) grunnleggende konsepter med fokus på værdata.

**Arkitektur**: Systemet består av tre hovedkomponenter:
- **Web Service**: Frontend brukergrensesnitt
- **AI Agent**: OpenAI-basert agent som orkestrerer forespørsler
- **MCP Server**: HTTP API med værfunksjonalitet

## Workshop Arkitektur (LAB01)

### Forenklet tjenestearkitektur
```
┌─────────────────┐    HTTP    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   Web Service   │ ─────────► │  Agent Service  │ ─────────► │  MCP Server     │
│   (Port 8080)   │            │   (Port 8001)   │            │   (Port 8000)   │
│                 │            │                 │            │                 │
│ • Frontend UI   │            │ • AI Logic      │            │ • Weather Tool  │
│ • User Interface│            │ • OpenAI GPT-4o │            │ • OpenWeatherMap│
│ • Examples      │            │ • Conversation  │            │ • Geocoding     │
│ • Health Checks │            │ • Memory        │            │ • Health Checks │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### 1. MCP Server (`services/mcp-server/`)
**HTTP API med dynamisk tools manifest** - Port 8000
- `GET /tools` - MCP tools manifest (følger MCP spesifikasjon)
- `POST /weather` - Værprognose for destinasjoner
- `POST /ping` - Ping test verktøy
- `GET /status` - Server status verktøy
- `GET /health` - Helsesjekk

**MCP Tools Manifest:**
Serveren eksponerer tilgjengelige verktøy via `/tools` endepunkt i henhold til MCP spesifikasjonen, inkludert navn, beskrivelse, input schema og endpoint informasjon.

**API som brukes:**
- **OpenWeatherMap** for værdata
- **Nominatim** (OpenStreetMap) for geocoding

### 2. Agent Service (`services/agent/`)
**AI-orkestrering med dynamisk tools loading** - Port 8001
- OpenAI GPT-4o mini for intelligent respons
- Dynamisk lasting av verktøy fra MCP server ved oppstart
- HTTP klient med intelligent endpoint mapping
- Persistent SQLite database for samtalehistorikk
- Eksplisitt og konvensjonsbasert endpoint mapping
- `POST /query` - Prosesser brukerforespørsler
- `GET /health` - Helsesjekk med agent status

### 3. Web Service (`services/web/`)  
**Frontend web-grensesnitt** - Port 8080
- HTML/JavaScript grensesnitt
- HTTP klient for agent kommunikasjon
- Eksempel spørsmål og interaktiv chat
- Real-time helsestatusindikator
- `GET /` - Hovedside
- `POST /query` - Proxy til agent service
- `GET /examples` - Foreslåtte spørsmål
- `GET /health` - Helsesjekk

## Workshop Læringsmål

Denne LAB01-versjonen er designet for å lære:
- **MCP Protocol**: Implementering av Model Context Protocol med dynamisk tools discovery
- **HTTP API**: REST API arkitektur med intelligent endpoint mapping
- **Tools Integration**: Dynamisk kobling av AI agent med MCP server verktøy
- **OpenAI Function Calling**: Strukturert verktøybruk med dynamic tool loading
- **Docker Deployment**: Containerisert mikroservice deployment
- **MCP Spesifikasjon**: Følge MCP standarder for tools manifest og endpoint eksponering

## Kom i gang

### Forutsetninger
Du trenger API nøkler for:
- **OpenAI**: For GPT AI → [platform.openai.com](https://platform.openai.com/)
- **OpenWeatherMap**: For værdata → [openweathermap.org/api](https://openweathermap.org/api)

### Docker Deployment (Anbefalt)
```bash
# Klon repository
git clone <repository-url>
cd agent

# Sett opp miljøvariabler
cp .env.example .env
# Rediger .env med dine API nøkler

# Start alle tjenester
docker-compose up -d

# Sjekk status
docker-compose ps
```

**Tilgang:**
- **Hovedside**: http://localhost:8080
- **Agent API**: http://localhost:8001  
- **MCP API**: http://localhost:8000

### Miljøvariabler
```bash
# Kreves for LAB01
OPENAI_API_KEY=your_openai_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here  

# Service URLs (auto-konfigurert i Docker)
MCP_SERVER_URL=http://mcp-server:8000
```

## Funksjoner (LAB01)

### Dynamisk Tools Discovery
- MCP server eksponerer tilgjengelige verktøy via `/tools` endpoint
- Agent laster verktøy dynamisk ved oppstart
- Intelligent mapping mellom verktøy og HTTP endpoints
- Støtte for eksplisitt endpoint spesifikasjon og konvensjonsbasert fallback

### Værprognose
- Detaljert værprognose for enhver destinasjon
- Temperatur, nedbør, vind og luftfuktighet
- Basert på OpenWeatherMap API

### MCP Verktøy
- **get_weather_forecast**: Hent værprognose for destinasjoner
- **ping**: Test verktøy for tilkoblingskontroll
- **get_status**: Server status informasjon
- Alle verktøy følger MCP spesifikasjon

### Persistent Hukommelse
- Husker samtalehistorikk på tvers av sesjoner
- SQLite database for lokal lagring
- Administrering av flere samtalesesjoner

### Intelligent Dialog
- OpenAI GPT-4o mini for naturlig språkforståelse
- Dynamic function calling basert på MCP tools manifest
- Kontekstbevisst samtaler

## MCP Arkitektur

Workshop LAB01 demonstrerer MCP (Model Context Protocol) arkitektur med dynamisk tools discovery:

```
Web Service → AI Agent ←→ MCP Server → External APIs
             ↓ (dynamic)   ↓ (/tools)
         Tools Loading  Tools Manifest
```

**Arkitektur komponenter:**
- **Web Service**: Frontend brukergrensesnitt og API proxy
- **AI Agent**: OpenAI GPT-4o mini med dynamisk tools loading og intelligent endpoint mapping
- **MCP Server**: HTTP API som eksponerer MCP tools manifest og implementerer verktøy
- **Tools Manifest**: MCP-kompatibel manifest med endpoint og method informasjon
- **Memory**: Persistent samtalehukommelse

**MCP Protocol Implementation:**
- MCP server følger MCP spesifikasjon for tools eksponering
- Agent implementerer dynamisk tools discovery ved oppstart
- Intelligent endpoint mapping med både eksplisitt og konvensjonsbasert støtte
- HTTP method routing (GET, POST, PUT, DELETE) basert på tools manifest

> **For detaljert workshop guide, se [WORKSHOP.md](./WORKSHOP.md)**

### Python Avhengigheter (hvis ikke bruker Docker)
```bash
pip install -r requirements.txt
```

## Docker Deployment (Anbefalt)

Systemet er optimalisert for Docker deployment med alle komponenter i separate containere.

### Forutsetninger
- Docker og Docker Compose installert
- API nøkler konfigurert (se over)

### Rask start
```bash
# Klon repository og naviger til mappen
cd travel-weather-mcp

# Kopier og rediger miljøvariabler
cp .env.example .env
# Rediger .env med dine API nøkler:
# - OPENAI_API_KEY (kreves)
# - OPENWEATHER_API_KEY (kreves)

# Bygg og start alle tjenester
docker-compose up -d

# Sjekk at alt kjører
docker-compose ps
```

### Tjenester som startes
- **travel-weather-mcp-server**: MCP server med værverktøy
- **travel-weather-agent**: AI agent service
- **travel-weather-web**: Web interface på http://localhost:8080

### Bruk av tjenestene

#### Web Interface
Åpne http://localhost:8080 i nettleseren for enkel bruk.

#### API Tilgang
```bash
# REST API kall
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hvordan er været i Oslo i dag?"}'
```

### Manuell Docker start
```bash
# Bygg og start alle tjenester
docker-compose up -d

# Eller start kun spesifikke tjenester
docker-compose up -d mcp-server travel-agent

# Se logfiler
docker-compose logs -f mcp-server
docker-compose logs -f travel-agent

# Stopp tjenester
docker-compose down
```

### Tilgjengelige tjenester
- **Web Interface**: http://localhost:8080 - Enkel web-grensesnitt for agenten
- **Agent API**: http://localhost:8001 - REST API for agenten
- **MCP Server**: http://localhost:8000 - MCP server API

## Bruk

### Web Interface (Anbefalt)
Gå til http://localhost:8080 i nettleseren din for et enkelt brukergrensesnitt.

### Docker Commands
```bash
# Se alle kjørende tjenester
docker-compose ps

# Restart spesifikk tjeneste
docker-compose restart mcp-server

# Se logfiler live
docker-compose logs -f travel-agent
```

## API Endpoints (LAB01)

### MCP Tools Discovery
- **GET /tools**: Hent MCP tools manifest med alle tilgjengelige verktøy
- **Returner**: JSON array med verktøy inkludert navn, beskrivelse, input schema, endpoint og HTTP method

### MCP Verktøy

#### get_weather_forecast
- **location**: Stedsnavn (f.eks. "Oslo, Norway")
- **Endpoint**: POST /weather
- **Returner**: Værprognose med temperatur, vind, fuktighet og beskrivelse

#### ping
- **message**: Melding å sende til ping verktøy
- **Endpoint**: POST /ping
- **Returner**: Bekreftelses-melding

#### get_status
- **Ingen parametere kreves**
- **Endpoint**: GET /status
- **Returner**: Server status informasjon

### Eksempel API kall
```bash
# Hent tools manifest fra MCP server
curl http://localhost:8000/tools

# Direkte verktøy kall til MCP server
curl -X POST http://localhost:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Oslo, Norway"}'

# Via Agent med dynamisk tools loading (anbefalt)
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hvordan er været i Oslo?"}'
```

## Sikkerhet

- API nøkler lagres som miljøvariabler
- Ingen sensitive data logges
- Input validering på alle endpoints
- Rate limiting gjennom OpenWeatherMap API

## Feilsøking

### Vanlige problemer

1. **"API key not configured"**
   - Sjekk at miljøvariabler er riktig satt i `.env`
   - Verifiser at API nøklene er gyldige

2. **"Location not found"**
   - Prøv mer spesifikke stedsnavn
   - Inkluder land (f.eks. "Oslo, Norway")

3. **Containerproblemer**
   - Kjør `docker-compose down && docker-compose up -d`
   - Sjekk logfiler med `docker-compose logs`

### Logging
```bash
# Se agent logfiler
docker-compose logs -f travel-agent

# Se MCP server logfiler
docker-compose logs -f mcp-server

# Se alle logfiler
docker-compose logs -f
```

## Workshop Utvidelser

LAB01 er designet for utvidelse. Deltagere kan legge til:

### Nye MCP verktøy
1. Definer en ny HTTP endpoint i `services/mcp-server/app.py`
2. Legg til verktøyet i tools array med endpoint og method informasjon
3. Agent vil automatisk laste det nye verktøyet ved restart via `/tools` manifest
4. Test med web interface

**Merk**: Agent laster verktøy dynamisk, så ingen hardkoding kreves i agent koden.

### Foreslåtte utvidelser
- **Ruteplanlegging**: Legg til OpenRouteService API
- **Hotell booking**: Integrer booking API
- **Transport**: Legg til public transport API
- **Oversettelse**: Legg til språkoversettelse

> **Se [WORKSHOP.md](./WORKSHOP.md) for detaljerte instruksjoner**

## Testing

### Manual testing
```bash
# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8080/health

# Test MCP tools manifest
curl http://localhost:8000/tools

# Test alle MCP verktøy
curl -X POST http://localhost:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Oslo, Norway"}'

curl -X POST http://localhost:8000/ping \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

curl http://localhost:8000/status
```

## Lisens

MIT License - se LICENSE fil for detaljer.

## Workshop Support

For workshop deltagere:
- **Dokumentasjon**: [WORKSHOP.md](./WORKSHOP.md)
- **Presentasjon**: [workshop-presentation.html](./workshop-presentation.html)
- **Teknisk support**: Spør workshopleder

## Bidrag

Bidrag er velkomne! Vennligst:
1. Fork repository
2. Opprett en feature branch
3. Commit endringene dine
4. Push til branch
5. Opprett en Pull Request