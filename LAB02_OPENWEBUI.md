# LAB02 OpenWebUI Integration

## Hva er OpenWebUI?

OpenWebUI er en moderne, brukervennlig webgrensesnitt for AI-chatbots som gir en ChatGPT-lignende opplevelse. Det er en åpen kildekode-løsning som kan brukes med forskjellige AI-modeller og API-er.

### Hovedfunksjoner:
- 🎨 Moderne og intuitiv chat-grensesnitt
- 💬 Støtte for samtalehistorikk
- 🔧 Konfigurerbar og tilpassbar
- 🔌 API-integrasjon med ulike AI-tjenester
- 📱 Responsiv design for desktop og mobil

## Implementering i LAB02

OpenWebUI er lagt til som en egen Docker-tjeneste i `docker-compose.yml`:

```yaml
openwebui:
  image: ghcr.io/open-webui/open-webui:latest
  ports:
    - "8002:8002"
  volumes:
    - openwebui:/app/backend/data
```

### Konfigurasjonsdetaljer:
- **Image**: Bruker den offisielle OpenWebUI Docker-imaget
- **Port**: Eksponert på port 8002 for å unngå konflikter med andre tjenester
- **Persistent Storage**: Data lagres i `openwebui` volume for å bevare samtaler og innstillinger

### Tilgang:
- **URL**: http://localhost:8002
- **Integrasjon**: Kan konfigureres til å bruke vår travel-weather-agent via API

## Fordeler med OpenWebUI

1. **Bedre brukeropplevelse**: Mer polert grensesnitt enn vår enkle web-tjeneste
2. **Samtalehistorikk**: Automatisk lagring og gjenoppretting av samtaler
3. **Konfigurerbarhet**: Kan tilpasses for spesifikke bruksområder
4. **Skalerbarhet**: Enkel å utvide med nye funksjoner og integrasjoner

## Integrasjon med LAB02 Backend

OpenWebUI kan integreres på to måter med vår eksisterende arkitektur:

### Alternativ 1: Kobling via Agent API (Port 8001)

OpenWebUI kan konfigureres til å kommunisere med travel-weather-agent som fungerer som en AI-proxy:

```bash
# Konfigurer OpenWebUI til å bruke agent som AI-backend
# I OpenWebUI admin panel:
# API Base URL: http://travel-agent:8001
# API Type: OpenAI Compatible
```

**Fordeler:**
- Direkte tilgang til AI-funksjonalitet med værverktøy
- Samtalehukommelse håndteres av agenten
- Ingen ekstra konfigurering av MCP protocol

### Alternativ 2: Direkte kobling med MCP Server (Port 8000) ⭐

Den mest kraftige løsningen er å koble OpenWebUI direkte til MCP serveren:

```bash
# Konfigurer OpenWebUI til å bruke MCP server
# I OpenWebUI admin panel:
# API Base URL: http://mcp-server:8000
# OpenAPI Spec URL: http://mcp-server:8000/openapi.json
```

**Hvorfor OpenAPI-støtte er en styrke:**

🔧 **Automatisk verktøyoppdagelse**: OpenWebUI kan automatisk lese OpenAPI-spesifikasjonen fra `http://mcp-server:8000/openapi.json` og oppdage alle tilgjengelige verktøy (weather, ping, status) uten manuell konfigurering.

📝 **Dynamisk dokumentasjon**: OpenAPI-spec gir komplett dokumentasjon av alle endpoints, parametere og returformater - OpenWebUI kan vise dette til brukerne.

🔄 **Automatisk oppdatering**: Når nye verktøy legges til MCP serveren, oppdateres OpenAPI-spec automatisk, og OpenWebUI får tilgang til nye funksjoner uten restart.

⚡ **Optimal ytelse**: Direkte kommunikasjon med MCP server eliminerer ett lag (agent) og gir raskere respons.

🛠️ **Full MCP Protocol støtte**: OpenWebUI kan utnytte alle MCP-funksjoner direkte, inkludert fremtidige utvidelser.

### Sammenligning: Agent vs MCP Server Integration

| Aspekt | Agent API (Port 8001) | MCP Server (Port 8000) |
|--------|----------------------|------------------------|
| **Arkitektur** | OpenWebUI → Agent → MCP → External APIs | OpenWebUI → MCP → External APIs |
| **Kompleksitet** | Høyere (flere lag) | Lavere (færre lag) |
| **Latens** | Høyere (ekstra hop via agent) | Lavere (direkte til MCP) |
| **AI-integrasjon** | Innebygd OpenAI-funksjonalitet | Kun verktøy/tools |

#### Alternativ 1: Agent API (Port 8001)

**✅ Fordeler:**
- **AI-behandling inkludert**: Agent håndterer både AI-respons og verktøykall
- **Samtalehukommelse**: Innebygd session management i agenten
- **Komplett løsning**: Én endpoint for alt (AI + tools)
- **Enklere frontend**: OpenWebUI trenger kun å sende tekst og motta svar
- **Robust error handling**: Agent kan håndtere feil og gi brukervennlige meldinger

**❌ Ulemper:**
- **Ekstra latens**: Request må gå gjennom agent-laget
- **Begrenset fleksibilitet**: Bundet til agent's AI-modell og logikk
- **Avhengighet**: Hvis agent feiler, blir hele systemet utilgjengelig
- **Ressursbruk**: Agent må kjøre kontinuerlig selv for enkle verktøykall

#### Alternativ 2: MCP Server (Port 8000)

**✅ Fordeler:**
- **Optimal ytelse**: Direkte kommunikasjon, minimale lag
- **Maksimal fleksibilitet**: OpenWebUI kan bruke sin egen AI-logikk
- **Skalerbarhet**: MCP server er lett og rask
- **OpenAPI-integrasjon**: Automatisk verktøyoppdagelse og dokumentasjon
- **Fremtidssikker**: Støtter full MCP protocol
- **Modulært design**: Verktøy kan utvikles og deployes uavhengig

**❌ Ulemper:**
- **Kun verktøy**: Ingen innebygd AI - OpenWebUI må håndtere AI-delen
- **Mer konfigurasjon**: Krever setup av AI-modell i OpenWebUI
- **Sammensatt arkitektur**: OpenWebUI må orkestrere AI + verktøykall
- **Ingen samtalehukommelse**: MCP server lagrer ikke session state

### Anbefaling basert på bruksområde:

**Velg Agent API (8001) hvis:**
- Du vil ha en "plug-and-play" løsning
- Enkel konfigurasjon er viktigst
- Du trenger kun grunnleggende chat-funksjonalitet

**Velg MCP Server (8000) hvis:**
- Ytelse og skalerbarhet er kritisk
- Du vil ha full kontroll over AI-modell og -logikk
- Du planlegger å utvide med mange flere verktøy
- Du vil utnytte OpenWebUI's avanserte funksjoner fullt ut

### Anbefalt arkitektur:

```
OpenWebUI (Port 8002) 
    ↓ OpenAPI integration
MCP Server (Port 8000)
    ↓ Tool endpoints
External APIs (Weather, etc.)
```

Dette gir oss det beste fra begge verdener:
- Robust backend-arkitektur med MCP protocol
- Moderne, brukervennlig frontend med OpenWebUI
- Automatisk verktøyoppdagelse via OpenAPI
- Optimal ytelse og fleksibilitet