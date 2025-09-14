# Travel Weather MCP Server og Agent

## 📚 Dokumentasjon

**➡️ [Komplett Dokumentasjon](./docs/README.md)** - Start her for full oversikt

### Viktige dokumenter:
- **[MCP Arkitektur & Template Guide](./docs/mcp-architecture-template.md)** - Detaljert arkitektur og mal for å lage egne agenter
- **[API Dokumentasjon](./docs/mcp-api-documentation.md)** - API referanse og verktøybeskrivelser  
- **[Integrasjonsguide](./docs/mcp-integration-guide.md)** - Praktiske eksempler
- **[OpenAPI Schema](./docs/mcp-openapi-schema.md)** - Teknisk spesifikasjon

## Oversikt

Dette prosjektet inneholder en Model Context Protocol (MCP) server og intelligent agent som kombinerer reisedata med værdata for å hjelpe med reiseplanlegging basert på værutsikter på destinasjonen.

**Siste oppdatering**: Systemet har blitt refaktorert for optimal Docker deployment med direkte funksjonalitet i stedet for subprocess MCP kommunikasjon.

## Komponenter

### MCP Server (`mcp_server.py`)
Tilbyr følgende verktøy:
- `get_weather_forecast`: Hent værprognose for en destinasjon (1-5 dager)
- `get_travel_routes`: Hent ruter og reiseinformasjon mellom to destinasjoner
- `plan_trip`: Kombiner reise- og værdata for optimal reiseplanlegging

**Gratis API-er som brukes:**
- OpenWeatherMap for værdata
- Nominatim (OpenStreetMap) for geocoding  
- OpenRouteService for rute-beregning (med fallback algoritmer)

### CLI Agent (`simple_agent.py`)
En kommandolinje agent som:
- Tar spørsmål som kommandolinjeargument eller interaktiv modus
- Bruker OpenAI GPT-4o for intelligent respons
- Har tilgang til alle værdata og reisedata verktøy
- **Huker tidligere samtaler** med persistent SQLite database
- Bruker direkte MCP funksjonalitet uten subprocess kommunikasjon

### Web Interface (`web_agent.py`)
En web-basert grensesnitt som:
- Tilbyr HTTP REST API på port 8080
- HTML interface for enkel bruk
- Samme funksjonalitet som CLI agent
- Optimalisert for Docker deployment

### Simplified Agent (`simple_agent.py`)
En forenklet agent klasse som:
- Bruker MCP server funksjonalitet direkte (ingen subprocess)
- Fungerer optimalt i Docker containere
- Deles av både CLI og web interface

## Funksjoner

### 🌤️ Værprognose
- Detaljert værprognose for enhver destinasjon
- 1-5 dagers prognoser
- Temperatur, nedbør, vind og luftfuktighet

### 🗺️ Reiseruter  
- Ruter og reiseinformasjon mellom destinasjoner
- Reiseavstand og tidsestimater
- Alternative transportmåter

### 🧳 Reiseplanlegging
- Kombinert vær- og reiseinformasjon
- Smarte anbefalinger basert på værforhold
- Optimal timing for reiser

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
