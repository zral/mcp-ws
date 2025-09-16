# Workshop: AI Agent med Model Context Protocol (MCP)

## 🎯 Oversikt

Denne workshopen lærer deg å bygge og utvide et AI agent-system som bruker **Model Context Protocol (MCP)** for å koble sammen AI-modeller med eksterne verktøy og tjenester.

### Hva du lærer:
- MCP arkitektur og konsepter
- Hvordan bygge egne MCP tools
- AI agent implementasjon med OpenAI
- Docker containerisering og deployment
- Utvidelse av systemet med nye verktøy

---

## 🏗️ Arkitektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   AI Agent      │    │   MCP Server    │
│                 │◄──►│                 │◄──►│                 │
│  (Simple HTML)  │    │   (OpenAI)      │    │   (Tools)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              │                        │
                              v                        v
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Conversation    │    │ External APIs   │
                    │ Memory (SQLite) │    │ (OpenWeather)   │
                    └─────────────────┘    └─────────────────┘
```

### Komponenter:

#### 1. **MCP Server** (`services/mcp-server/`)
- **Rolle**: Tilbyr verktøy (tools) som AI-agenten kan bruke
- **Protokoll**: HTTP API som implementerer MCP-standarder
- **Eksempel tools**: Værdata, reiseruter, e-post (fjernet i LAB01)

#### 2. **AI Agent** (`services/agent/`)
- **Rolle**: Intelligent samtaleagent som bruker OpenAI
- **Funksjon**: Prosesserer brukerforespørsler og kaller MCP tools
- **Memory**: Lagrer samtalehistorikk i SQLite

#### 3. **Web Interface** (`services/web/`)
- **Rolle**: Enkel brukergrensesnitt for testing
- **Type**: Static HTML med JavaScript

---

## 🛠️ MCP Tool Development

### Konsepter

**Model Context Protocol (MCP)** er en standard for å koble AI-modeller med eksterne verktøy og datakilder på en sikker og strukturert måte.

#### Tool Definition
Hvert tool har:
- **Navn**: Unikt navn som AI-en bruker
- **Beskrivelse**: Forklarer hva toolet gjør
- **Parametere**: Input-skjema (JSON Schema)
- **Implementation**: Python-funksjon som utfører arbeidet

### Eksempel: Vær Tool

```python
# I services/mcp-server/app.py

@app.post("/tools/get_weather_forecast")
async def get_weather_forecast(request: WeatherRequest):
    """
    Hent værvarsel for en gitt lokasjon.
    
    Args:
        request: WeatherRequest med location og days
    
    Returns:
        JSON med værdata fra OpenWeatherMap
    """
    try:
        # 1. Konverter lokasjon til koordinater
        coords = await geocode_location(request.location)
        
        # 2. Hent værdata fra OpenWeatherMap
        weather_data = await fetch_weather_data(coords)
        
        # 3. Returner strukturert data
        return {
            "success": True,
            "location": request.location,
            "forecast": weather_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Tool Registration

```python
# Tool metadata for AI-agenten
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Hent værvarsel for en bestemt lokasjon",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Navnet på byen/stedet"
                    },
                    "days": {
                        "type": "integer", 
                        "description": "Antall dager værvarsel (1-5)",
                        "default": 3
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

---

## 🚀 Legge til nye Tools

### Steg 1: Definer Tool Function

Legg til i `services/mcp-server/app.py`:

```python
from pydantic import BaseModel

# Request model
class NewsRequest(BaseModel):
    topic: str
    language: str = "no"

# Tool implementation  
@app.post("/tools/get_news")
async def get_news(request: NewsRequest):
    """Hent nyheter om et bestemt emne."""
    try:
        # Din implementasjon her
        news_data = await fetch_news_from_api(request.topic, request.language)
        
        return {
            "success": True,
            "topic": request.topic,
            "articles": news_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Legg til health check info
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools": ["get_weather_forecast", "get_news"],  # Oppdater liste
        "timestamp": datetime.now().isoformat()
    }
```

### Steg 2: Registrer i Agent

Legg til i `services/agent/app.py`:

```python
# Utvid TOOLS array
self.tools = [
    {
        "type": "function", 
        "function": {
            "name": "get_weather_forecast",
            "description": "Hent værvarsel for en bestemt lokasjon",
            "parameters": {
                # ... eksisterende weather tool
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news", 
            "description": "Hent aktuelle nyheter om et bestemt emne",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Emnet å søke nyheter om"
                    },
                    "language": {
                        "type": "string", 
                        "description": "Språkkode (no, en, etc.)",
                        "default": "no"
                    }
                },
                "required": ["topic"]
            }
        }
    }
    # Legg til flere tools her...
]
```

### Steg 3: Håndter Tool Calls

Agenten håndterer automatisk nye tools, men du kan tilpasse logikken:

```python
# I agent conversation method
for tool_call in response_message.tool_calls:
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    
    # Kall MCP server
    tool_result = await self.call_mcp_tool(tool_name, tool_args)
    
    # Legg til result i samtale
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(tool_result)
    })
```

---

## 🐳 Docker Development

### Prosjektstruktur

```
agent/
├── docker-compose.yml          # Hovedkonfigurasjon
├── .env.example               # Miljøvariabler mal
├── services/
│   ├── mcp-server/
│   │   ├── Dockerfile         # MCP server container
│   │   ├── requirements.txt   # Python avhengigheter
│   │   └── app.py            # Server implementasjon
│   ├── agent/
│   │   ├── Dockerfile         # Agent container  
│   │   ├── requirements.txt   # Python avhengigheter
│   │   ├── app.py            # Agent implementasjon
│   │   └── conversation_memory.py
│   └── web/
│       ├── Dockerfile         # Web server container
│       └── index.html        # Frontend
└── logs/                     # Shared logging volume
```

### Environment Setup

1. **Kopier environment fil:**
```bash
cp .env.example .env
```

2. **Legg inn API-nøkler:**
```bash
# .env file
OPENAI_API_KEY=your-openai-api-key-here
OPENWEATHER_API_KEY=your-openweather-api-key-here
```

### Build og Deploy

#### Enkelt kommandoer:

```bash
# Start alt fra scratch
docker-compose up --build

# Stop alle tjenester
docker-compose down

# Rebuild kun én tjeneste
docker-compose build mcp-server
docker-compose up -d mcp-server

# Se logger
docker-compose logs -f travel-agent
docker-compose logs --tail=50 mcp-server
```

#### Development workflow:

```bash
# 1. Stopp eksisterende
docker-compose down

# 2. Bygg endringer
docker-compose build travel-agent

# 3. Start på nytt
docker-compose up -d

# 4. Test endringer
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Test my changes"}'
```

### Service URLs

- **Agent API**: http://localhost:8001
- **MCP Server**: http://localhost:8000  
- **Web Interface**: http://localhost:3000

### Health Checks

```bash
# Sjekk alle tjenester
docker-compose ps

# Sjekk spesifikke endpoints
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Agent API
```

---

## 🧪 Testing og Debugging

### API Testing

```bash
# Test weather tool direkte
curl -X POST "http://localhost:8000/tools/get_weather_forecast" \
  -H "Content-Type: application/json" \
  -d '{"location": "Oslo", "days": 3}'

# Test agent med conversation
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hva er været i Bergen?"}'
```

### Debugging Tips

1. **Se logger i sanntid:**
```bash
docker-compose logs -f travel-agent
```

2. **Gå inn i container:**
```bash
docker-compose exec travel-agent bash
```

3. **Sjekk environment variabler:**
```bash
docker-compose exec travel-agent env | grep API
```

4. **Test MCP connection:**
```python
# Fra agent container
import httpx
response = httpx.get("http://mcp-server:8000/health")
print(response.json())
```

---

## 📝 Oppgaver

### Øvelse 1: Legg til nytt Weather Feature
Utvid weather tool til å inkludere:
- UV-indeks
- Luftkvalitet 
- Soloppgang/solnedgang

### Øvelse 2: Implementer News Tool
Lag et nytt tool som:
- Henter nyheter fra en API (f.eks. NewsAPI)
- Filtrerer på språk og kategori
- Returnerer sammendrag

### Øvelse 3: Legg til Memory Features
Utvid agent til å:
- Huske brukerpreferanser
- Gi personaliserte anbefalinger
- Lage brukerprofiles

### Øvelse 4: Advanced Tool Integration
Implementer:
- Kartintegrasjon (Google Maps)
- Kalendersynkronisering
- E-post notifikasjoner

---

## 🔧 Production Considerations

### Sikkerhet
- API-nøkkel håndtering
- Input validering
- Rate limiting
- HTTPS certificates

### Skalering 
- Load balancing
- Database clustering
- Horizontal scaling med Docker Swarm/Kubernetes

### Monitoring
- Logging aggregering
- Metrics samling
- Error tracking
- Performance monitoring

---

## 📚 Ressurser

- [Model Context Protocol Dokumentasjon](https://modelcontextprotocol.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Docker Compose Guide](https://docs.docker.com/compose/)
- [FastAPI Dokumentasjon](https://fastapi.tiangolo.com/)

---

## 🤝 Support

For spørsmål eller problemer:
1. Sjekk logger: `docker-compose logs`
2. Verify environment: `cat .env`
3. Test connections: `curl health endpoints`
4. Rebuild if needed: `docker-compose build --no-cache`

**Happy coding! 🚀**