# Ingrids Reisetjenester - Mikroservice Arkitektur

## 📚 Dokumentasjon

**➡️ [Komplett Dokumentasjon](./docs/README.md)** - Start her for full oversikt

### Viktige dokumenter:
- **[MCP Arkitektur & Template Guide](./docs/mcp-architecture-template.md)** - Detaljert arkitektur og mal for å lage egne agenter
- **[API Dokumentasjon](./docs/mcp-api-documentation.md)** - API referanse og verktøybeskrivelser  
- **[Integrasjonsguide](./docs/mcp-integration-guide.md)** - Praktiske eksempler
- **[Docker Deployment Guide](./docs/docker-deployment.md)** - Deployment og drift
- **[OpenAPI Schema](./docs/mcp-openapi-schema.md)** - Teknisk spesifikasjon

## Oversikt

**Ingrids Reisetjenester** er en intelligent reiseplanlegging plattform bygget med mikroservice-arkitektur. Systemet kombinerer reisedata med værdata for å gi personlige reiseanbefalinger basert på værutsikter på destinasjonen.

**Arkitektur**: Systemet er bygget som tre separate HTTP-baserte mikrotjenester som kommuniserer via REST API.

## 🏗️ Mikroservice Arkitektur

### Tjenestearkitektur
```
┌─────────────────┐    HTTP    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   Web Service   │ ─────────► │  Agent Service  │ ─────────► │  MCP Server     │
│   (Port 8080)   │            │   (Port 8001)   │            │   (Port 8000)   │
│                 │            │                 │            │                 │
│ • Frontend UI   │            │ • AI Logic      │            │ • Tools/APIs    │
│ • User Interface│            │ • OpenAI GPT-4o │            │ • Weather Data  │
│ • Examples      │            │ • Conversation  │            │ • Route Calc    │
│ • Health Checks │            │ • Memory        │            │ • Trip Planning │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### 1. MCP Server (`services/mcp-server/`)
**HTTP API for reiseverktøy** - Port 8000
- `POST /weather` - Værprognose for destinasjoner  
- `POST /routes` - Ruteberegning mellom steder
- `POST /plan` - Komplett reiseplanlegging
- `GET /health` - Helsesjekk

**API-er som brukes:**
- OpenWeatherMap for værdata
- Nominatim (OpenStreetMap) for geocoding  
- OpenRouteService for rute-beregning (med fallback algoritmer)

### 2. Agent Service (`services/agent/`)
**AI-orkestrering med OpenAI** - Port 8001
- OpenAI GPT-4o for intelligent respons
- HTTP klient for MCP server kommunikasjon
- Persistent SQLite database for samtalehistorikk
- Function calling for verktøybruk
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

## 🚀 Kom i gang

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
# Kreves
OPENAI_API_KEY=your_openai_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here  

# Valgfrie
OPENROUTE_API_KEY=your_openroute_api_key_here # For bedre ruter

# E-post konfigurasjon (for e-post funksjonalitet)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Gmail app-passord
FROM_EMAIL=your-email@gmail.com
```
- API nøklene deles av alle tjenester
- E-post konfigurasjon aktiverer "📧 Send på e-post" funksjonaliteten

## Funksjoner

### 🌤️ Værprognose
- Detaljert værprognose for enhver destinasjon
- 1-5 dagers prognoser
- Temperatur, nedbør, vind og luftfuktighet

### 🗺️ Reiseruter  
- Ruter og reiseinformasjon mellom destinasjoner
- Reiseavstand og tidsestimater
- Alternative transportmåter
- Detaljerte navigasjonsinstruksjoner med bold formatering

### 🧳 Reiseplanlegging
- Kombinert vær- og reiseinformasjon
- Smarte anbefalinger basert på værforhold
- Optimal timing for reiser

### 📧 E-post Integration
- **Send reiseinfo direkte på e-post** med "📧 Send på e-post" knappen
- Automatisk formatering med HTML og markdown styling
- SMTP support via Gmail eller andre leverandører
- Professional e-post design med bold veinavnsprisser og ruter

### 🧠 Persistent Hukommelse
- Husker samtalehistorikk på tvers av sesjoner
- SQLite database for lokal lagring
- Administrering av flere samtalesesjoner

## 🏗️ Systemarkitektur

Systemet bruker en modulær MCP (Model Context Protocol) arkitektur:

```
🌐 Web/CLI Interface → 🤖 AI Agent → 🔧 MCP Tools → 🌍 External APIs
```

- **MCP Server**: Rene verktøyfunksjoner (vær, ruter, planlegging)
- **AI Agent**: OpenAI GPT-4o med Function Calling
- **REST API**: HTTP grensesnitt for integrasjon
- **Memory**: Persistent samtalehukommelse

> **💡 For detaljert arkitekturinformasjon, se [MCP Arkitektur & Template Guide](./docs/mcp-architecture-template.md)**

## Forutsetninger

### API Nøkler

Du trenger API nøkler for:
- **OpenWeatherMap**: For værdata → [openweathermap.org/api](https://openweathermap.org/api)
- **OpenAI**: For GPT-4 AI → [platform.openai.com](https://platform.openai.com/)
- **OpenRouteService**: For ruter (valgfri) → [openrouteservice.org](https://openrouteservice.org/)

Sett disse i `.env` filen (kopier fra `.env.example`).

### Python Avhengigheter (hvis ikke bruker Docker)
```bash
pip install -r requirements.txt
```

## Docker Deployment (Anbefalt)

Systemet er optimalisert for Docker deployment med alle komponenter i separate containere.

### Forutsetninger
- Docker og Docker Compose installert
- API nøkler konfigurert

### Rask start
```bash
# Klon repository og naviger til mappen
cd travel-weather-mcp

# Kopier og rediger miljøvariabler
cp .env.example .env
# Rediger .env med dine API nøkler:
# - OPENAI_API_KEY (kreves)
# - OPENWEATHER_API_KEY (kreves)
# - OPENROUTE_API_KEY (valgfri)

# Bygg og start alle tjenester
docker-compose up -d

# Sjekk at alt kjører
docker-compose ps
```

### Tjenester som startes
- **travel-weather-mcp-server**: MCP server (kjører på demand)
- **travel-weather-agent**: CLI agent container (kjører i bakgrunnen)
- **travel-weather-web**: Web interface på http://localhost:8080

### Bruk av tjenestene

#### Web Interface
Åpne http://localhost:8080 i nettleseren for enkel bruk.

#### CLI Agent
```bash
# Enkelt spørsmål
docker exec -it travel-weather-agent python simple_agent.py "Hvordan er været i Oslo i dag?"

# Interaktiv modus
docker exec -it travel-weather-agent python simple_agent.py
```

#### API Tilgang
```bash
# REST API kall
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Planlegg en reise fra Oslo til Bergen i morgen"}'
```

### Manuell Docker start
```bash
# Bygg og start alle tjenester
docker-compose up -d

# Eller start kun spesifikke tjenester
docker-compose up -d mcp-server agent-web

# Se logfiler
docker-compose logs -f mcp-server
docker-compose logs -f agent-web

# Stopp tjenester
docker-compose down
```

### Tilgjengelige tjenester
- **Web Interface**: http://localhost:8080 - Enkel web-grensesnitt for agenten
- **MCP Server**: Port 8001 - MCP server for andre klienter
- **Agent Web API**: Port 8002 - REST API for agenten
- **MCP Inspector**: http://localhost:5173 - Debugging (kun med `--profile debug`)

### Testing med MCP Inspector
```bash
# Start med debug profil
docker-compose --profile debug up -d

# Gå til http://localhost:5173 for debugging
```

## Bruk

### 🌐 Web Interface (Anbefalt)
Gå til http://localhost:8080 i nettleseren din for et enkelt brukergrensesnitt.

### 🐳 Docker Commands
```bash
# Interaktiv agent i terminal
docker-compose exec travel-agent python simple_agent.py

# Se alle kjørende tjenester
docker-compose ps

# Restart spesifikk tjeneste
docker-compose restart mcp-server

# Se logfiler live
docker-compose logs -f agent-web
```

### 🔍 Debugging
```bash
# Start MCP Inspector for debugging
docker-compose --profile debug up mcp-inspector

# Gå til http://localhost:5173
```

## API Endpoints

### get_weather_forecast
- **location**: Stedsnavn (f.eks. "Oslo, NO")
- **days**: Antall dager (1-5)

### get_travel_routes
- **origin**: Startpunkt
- **destination**: Destinasjon
- **mode**: Reisemåte ("driving", "walking", "bicycling", "transit")

### plan_trip
- **origin**: Startpunkt
- **destination**: Destinasjon
- **travel_date**: Reisedato (YYYY-MM-DD)
- **mode**: Reisemåte

## Sikkerhet

- API nøkler lagres som miljøvariabler
- Ingen sensitive data logges
- Input validering på alle endpoints
- Rate limiting gjennom API providers

## Feilsøking

### Vanlige problemer

1. **"API key not configured"**
   - Sjekk at miljøvariabler er riktig satt
   - Verifiser at API nøklene er gyldige

2. **"Location not found"**
   - Prøv mer spesifikke stedsnavn
   - Inkluder land (f.eks. "Oslo, Norway")

3. **"No routes found"**
   - Sjekk stavemåte på steder
   - Prøv alternative reisemåter

### Logging
Serveren logger til stderr. For debugging:
```bash
python mcp_server.py 2>debug.log
```

## Utvikling

### Legge til nye verktøy
1. Definer en ny funksjon med `@mcp.tool()` dekoratør
2. Legg til dokumentasjon og type hints
3. Implementer feilhåndtering
4. Test med MCP Inspector

### Testing
```bash
# Test med MCP Inspector
npx @modelcontextprotocol/inspector python mcp_server.py

# Test agent
python -m pytest tests/
```

## Lisens

MIT License - se LICENSE fil for detaljer.

## Bidrag

Bidrag er velkomne! Vennligst:
1. Fork repository
2. Opprett en feature branch
3. Commit endringene dine
4. Push til branch
5. Opprett en Pull Request
