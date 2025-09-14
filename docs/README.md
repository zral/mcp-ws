# Ingrids Reisetjenester - Dokumentasjonsindeks

## 📖 Komplett dokumentasjonsoversikt

Denne dokumentasjonen gir deg alt du trenger for å forstå, deploye og utvide **Ingrids Reisetjenester** mikroservice-arkitektur.

### 🎯 Kom i gang raskt

1. **[Mikroservice Arkitektur Guide](./microservice-architecture.md)** - **Start her!** Komplett arkitekturovesikt
2. **[Docker Deployment Guide](./docker-deployment.md)** - Deploy systemet lokalt eller i produksjon  
3. **[API Dokumentasjon](./mcp-api-documentation.md)** - HTTP API referanse for alle tjenester
4. **[Integrasjonsguide](./mcp-integration-guide.md)** - Praktiske eksempler på bruk

### 🏗️ For utviklere

5. **[MCP Arkitektur & Template Guide](./mcp-architecture-template.md)** - Bygg egne MCP-baserte agenter
6. **[OpenAPI Schema](./mcp-openapi-schema.md)** - Teknisk API spesifikasjon

## 📋 Dokumentasjonsstruktur

```
docs/
├── README.md                        # Denne filen - dokumentasjonsindeks
├── microservice-architecture.md     # ⭐ Hovedarkitekturguide  
├── docker-deployment.md            # Deployment og drift
├── mcp-api-documentation.md         # HTTP API referanse
├── mcp-integration-guide.md         # Integrasjonseksempler
├── mcp-architecture-template.md     # MCP utviklermal
├── mcp-openapi-schema.md           # OpenAPI 3.0 spesifikasjon
├── memory.md                       # Samtalehukommelse
└── free-apis.md                    # Eksterne API-er som brukes
```

## 🚀 Bruksscenarier

### For utviklere som vil:

- **Deploy systemet**: [Docker Deployment Guide](./docker-deployment.md)
- **Forstå arkitekturen**: [Mikroservice Arkitektur Guide](./microservice-architecture.md)  
- **Bruke API-ene**: [API Dokumentasjon](./mcp-api-documentation.md)
- **Integrere i eksisterende system**: [Integrasjonsguide](./mcp-integration-guide.md)
- **Bygge lignende agenter**: [MCP Template Guide](./mcp-architecture-template.md)

### For product managers/arkitekter:

- **Evaluere løsningen**: [Mikroservice Arkitektur](./microservice-architecture.md) + [API Dokumentasjon](./mcp-api-documentation.md)
- **Planlegge deployment**: [Docker Deployment Guide](./docker-deployment.md)
- **Forstå muligheter**: [Integrasjonsguide](./mcp-integration-guide.md)

## 🏗️ Systemarkitektur (Sammendrag)

**Ingrids Reisetjenester** består av tre HTTP-baserte mikrotjenester:

```
┌─────────────────┐    HTTP     ┌─────────────────┐    HTTP     ┌─────────────────┐
│   Web Service   │ ─────────► │  Agent Service  │ ─────────► │  MCP Server     │
│   (Port 8080)   │            │   (Port 8001)   │            │   (Port 8000)   │
│                 │            │                 │            │                 │
│ • Frontend UI   │            │ • OpenAI GPT-4o │            │ • Weather APIs  │
│ • User Interface│            │ • Conversation  │            │ • Route Calc    │
│ • Examples      │            │ • Memory        │            │ • Trip Planning │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### Tjenester:

- **Web Service** (`services/web/`): Frontend og brukergrensesnitt
- **Agent Service** (`services/agent/`): AI-orkestrering med OpenAI GPT-4o  
- **MCP Server** (`services/mcp-server/`): Verktøy-API for vær og reisedata

## 💡 Key Concepts

### Mikroservice Arkitektur
- **Formål**: Modulær, skalerbar og vedlikeholdbar tjenesteoppdeling
- **Kommunikasjon**: HTTP REST API-er mellom tjenester
- **Deployment**: Docker Compose med isolerte containere
- **Skalering**: Hver tjeneste kan skaleres uavhengig

### Model Context Protocol (MCP)  
- **Formål**: Standardisert måte å koble AI-modeller med verktøy/tjenester
- **Implementasjon**: HTTP API wrapper rundt MCP funksjoner
- **Fordeler**: Gjenbrukbare verktøy på tvers av AI-agenter
- **Fordeler**: Modulær, skalerbar, testbar arkitektur
- **Implementasjon**: Rene async Python-funksjoner

### AI Agent Architecture
- **AI Layer**: OpenAI GPT med Function Calling
- **Tool Layer**: MCP verktøy for spesifikke oppgaver
- **API Layer**: REST endpoints for integrasjon
- **Memory**: Persistent samtalehukommelse

### Travel Weather Domene
- **Værdata**: OpenWeatherMap integration
- **Ruteberegning**: OpenRouteService for nøyaktige reiseruter
- **Planlegging**: Kombinasjon av vær- og rutedata

## 🔧 Teknisk Stack

- **Python 3.11+**: Core runtime
- **OpenAI GPT-4o**: AI reasoning og Function Calling
- **FastAPI**: REST API framework
- **SQLite**: Persistent storage
- **Docker**: Containerisering og deployment
- **Async/Await**: Høy ytelse ved API-kall

## 📊 Sammendrag av dokumenter

| Dokument | Fokus | Målgruppe | Lengde |
|----------|-------|-----------|--------|
| [API Dokumentasjon](./mcp-api-documentation.md) | Referanse, eksempler | Alle | Medium |
| [Arkitektur & Template](./mcp-architecture-template.md) | Dypforståelse, utvidelse | Utviklere | Lang ⭐ |
| [OpenAPI Schema](./mcp-openapi-schema.md) | Teknisk spec | Integratører | Medium |
| [Integrasjonsguide](./mcp-integration-guide.md) | Praktiske eksempler | Utviklere | Medium |

---

> **💡 Anbefaling**: Start med [API Dokumentasjon](./mcp-api-documentation.md) for grunnleggende forståelse, og gå deretter til [Arkitektur & Template Guide](./mcp-architecture-template.md) for å forstå hvordan du kan bygge egne agenter med MCP.
