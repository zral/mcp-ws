# Travel Weather MCP Server og Agent

## Oversikt

Dette prosjektet inneholder en Model Context Protocol (MCP) server og agent som kombinerer reisedata fra Google med værdata fra OpenWeatherMap for å hjelpe med reiseplanlegging basert på værutsikter på destinasjonen.

## Komponenter

### MCP Server (`mcp_server.py`)
Tilbyr følgende verktøy:
- `get_weather_forecast`: Hent værprognose for en destinasjon (1-5 dager)
- `get_travel_routes`: Hent ruter og reiseinformasjon mellom to destinasjoner
- `plan_trip`: Kombiner reise- og værdata for optimal reiseplanlegging

### Agent (`agent.py`)
En intelligent agent som bruker MCP serveren til å:
- Svare på spørsmål om vær på destinasjoner
- Gi reiseråd basert på værforhold
- Planlegge komplette reiser med vær- og ruteinformasjon

## Forutsetninger

### API Nøkler
## API Nøkler

Du trenger API nøkler for:
- **OpenWeatherMap**: For værdata → [openweathermap.org/api](https://openweathermap.org/api)
- **Google Maps**: For reisedata → [console.cloud.google.com](https://console.cloud.google.com/)
- **Anthropic**: For Claude AI → [console.anthropic.com](https://console.anthropic.com/)

Sett disse i `.env` filen (kopier fra `.env.example`).

### Python Avhengigheter (hvis ikke bruker Docker)
```bash
pip install -r requirements.txt
```

## API Nøkler

## Docker Oppsett (Anbefalt)

Alle komponenter kjører i Docker containere - ingen installasjon på host-maskinen kreves.

### Forutsetninger
- Docker og Docker Compose installert
- API nøkler (se under)

### Rask start
```bash
# Klon repository
git clone <repository-url>
cd travel-weather-mcp

# Kopier og rediger miljøvariabler
cp .env.example .env
# Rediger .env med dine API nøkler

# Start alle tjenester
./start.sh
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
docker-compose exec travel-agent python agent.py

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
