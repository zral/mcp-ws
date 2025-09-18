# MCP Travel Weather Server - Dokumentasjonsindeks

## 📖 Komplett dokumentasjonsoversikt

Denne dokumentasjonen gir deg alt du trenger for å forstå, deploye og utvide **MCP Travel Weather Server** mikroservice-arkitektur med Model Context Protocol (MCP) implementasjon.

### 🎯 Kom i gang raskt

1. **[Mikroservice Arkitektur Guide](./microservice-architecture.md)** - **Start her!** MCP arkitekturovesikt
2. **[Docker Deployment Guide](./docker-deployment.md)** - Deploy systemet lokalt eller i produksjon  
3. **[API Dokumentasjon](./mcp-api-documentation.md)** - HTTP API referanse for alle tjenester
4. **[MCP Integration Guide](./mcp-integration-guide.md)** - MCP protocol implementasjon og bruk

### 🏗️ For utviklere

5. **[MCP Arkitektur & Template Guide](./mcp-architecture-template.md)** - Bygg egne MCP-baserte agenter
6. **[OpenAPI Schema](./mcp-openapi-schema.md)** - Teknisk API spesifikasjon

## 📋 Dokumentasjonsstruktur

```
docs/
├── README.md                        # Denne filen - dokumentasjonsindeks
├── microservice-architecture.md     # ⭐ MCP arkitekturguide  
├── docker-deployment.md            # Deployment og drift
├── mcp-api-documentation.md         # HTTP API referanse med MCP endpoints
├── mcp-integration-guide.md         # MCP protocol integrasjonseksempler
├── mcp-architecture-template.md     # MCP utviklermal
├── mcp-openapi-schema.md           # OpenAPI 3.0 spesifikasjon
├── memory.md                       # Samtalehukommelse
└── free-apis.md                    # Eksterne API-er som brukes
```

## 🚀 Bruksscenarier

### For utviklere som vil:

- **Deploy systemet**: [Docker Deployment Guide](./docker-deployment.md)
- **Forstå MCP arkitekturen**: [Mikroservice Arkitektur Guide](./microservice-architecture.md)  
- **Bruke MCP API-ene**: [API Dokumentasjon](./mcp-api-documentation.md)
- **Implementere MCP protocol**: [MCP Integration Guide](./mcp-integration-guide.md)
- **Bygge MCP agenter**: [MCP Template Guide](./mcp-architecture-template.md)

### For product managers/arkitekter:

- **Evaluere MCP løsningen**: [Mikroservice Arkitektur](./microservice-architecture.md) + [API Dokumentasjon](./mcp-api-documentation.md)
- **Planlegge deployment**: [Docker Deployment Guide](./docker-deployment.md)
- **Forstå MCP protokoll**: [MCP Integration Guide](./mcp-integration-guide.md)

## 🏗️ MCP Systemarkitektur (Sammendrag)

**Ingrids Reisetjenester** består av tre HTTP-baserte mikrotjenester:

```
┌─────────────────┐    HTTP     ┌─────────────────┐    HTTP     ┌─────────────────┐
│   Web Service   │ ─────────► │  Agent Service  │ ─────────► │  MCP Server     │
│   (Port 8080)   │            │   (Port 8001)   │            │   (Port 8000)   │
│                 │            │                 │            │                 │
│ • Frontend UI   │            │ • OpenAI GPT-4o │            │ • Weather APIs  │
**MCP Travel Weather Server** består av tre mikrotjenester med MCP protocol implementasjon:

```
Web Service (8080) → Agent Service (8001) ↔ MCP Server (8000)
│ • User Interface│    │ • Dynamic Tools  │    │ • Tools Manifest│
│ • Examples      │    │ • AI Logic       │    │ • Weather API   │
└─────────────────┘    │ • MCP Client     │    │ • HTTP Router   │
                       └─────────────────┘    └─────────────────┘
```

### Tjenester:

- **Web Service** (`services/web/`): Frontend og brukergrensesnitt
- **Agent Service** (`services/agent/`): AI-orkestrering med dynamisk tools loading  
- **MCP Server** (`services/mcp-server/`): MCP-kompatibel tools manifest og endpoints

## 💡 Key Concepts

### MCP Protocol Implementation
- **Tools Discovery**: Dynamisk lasting av verktøy via `/tools` manifest
- **Endpoint Mapping**: Intelligent routing mellom tools og HTTP endpoints  
- **HTTP Method Support**: GET, POST, PUT, DELETE routing
- **Schema Validation**: JSON schema for alle MCP verktøy

### Mikroservice Arkitektur
- **Formål**: Modulær, skalerbar og vedlikeholdbar tjenesteoppdeling
- **Kommunikasjon**: HTTP REST API-er med MCP protocol compliance
- **Deployment**: Docker Compose med isolerte containere
- **Skalering**: Hver tjeneste kan skaleres uavhengig

### AI Agent Architecture
- **AI Layer**: OpenAI GPT med Dynamic Function Calling
- **MCP Layer**: Protocol-compliant tools loading og mapping
- **Tool Layer**: MCP verktøy for spesifikke oppgaver
- **API Layer**: REST endpoints for integrasjon
- **Memory**: Persistent samtalehukommelse

### Workshop Learning Design
- **Pedagogisk tilnærming**: Agent laster 3 verktøy men er begrenset til weather-only
- **Læring**: Deltagere oppdager begrensninger og lærer å aktivere alle verktøy
- **MCP Discovery**: Hands-on erfaring med dynamisk tools loading

## 🔧 Teknisk Stack

- **Python 3.11+**: Core runtime
- **Model Context Protocol (MCP)**: Tools discovery standard
- **OpenAI GPT-4o**: AI reasoning og Dynamic Function Calling
- **FastAPI**: REST API framework med MCP endpoints
- **SQLite**: Persistent storage
- **Docker**: Containerisering og deployment
- **Async/Await**: Høy ytelse ved API-kall

## 📊 Sammendrag av dokumenter

| Dokument | Fokus | Målgruppe | Lengde |
|----------|-------|-----------|--------|
| [API Dokumentasjon](./mcp-api-documentation.md) | MCP API referanse | Alle | Medium |
| [MCP Integration Guide](./mcp-integration-guide.md) | MCP protocol eksempler | Utviklere | Medium ⭐ |
| [Arkitektur Guide](./microservice-architecture.md) | MCP arkitektur | Utviklere | Lang |
| [OpenAPI Schema](./mcp-openapi-schema.md) | Teknisk spec | Integratører | Medium |

---

> **💡 Anbefaling**: Start med [MCP Integration Guide](./mcp-integration-guide.md) for å forstå MCP protocol implementasjon, og gå deretter til [API Dokumentasjon](./mcp-api-documentation.md) for komplett referanse.
