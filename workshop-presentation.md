---
marp: true
theme: default
paginate: true
backgroundColor: #1e1e1e
color: #ffffff
header: '🤖 AI Agent Workshop - Model Context Protocol'
footer: 'Lars Søraas | September 2025'
style: |
  section {
    font-size: 24px;
    line-height: 1.3;
    padding: 40px;
  }
  h1 {
    font-size: 42px;
    margin-bottom: 0.4em;
    margin-top: 0.2em;
  }
  h2 {
    font-size: 32px;
    margin-bottom: 0.3em;
    margin-top: 0.2em;
  }
  h3 {
    font-size: 28px;
    margin-bottom: 0.2em;
    margin-top: 0.2em;
  }
  li {
    margin-bottom: 0.2em;
  }
  code {
    font-size: 18px;
  }
  pre {
    font-size: 16px;
    line-height: 1.2;
    margin: 0.5em 0;
  }
  ul, ol {
    margin: 0.5em 0;
  }
---

<!-- _class: lead -->
# 🤖 AI Agent Workshop
## AI Agenter med Model Context Protocol (MCP)

**Lars Søraas**  
*September 2025*

---

# 🎯 Læringsmål

- **Forstå** MCP arkitektur og konsepter
- **Bygge** din egen AI agent med verktøy
- **Utvide** systemet med nye funksjoner
- **Deploye** ved hjelp av Docker containere
- **Lære** beste praksis for produksjon

---

# 🗓️ Agenda

1. **Introduksjon til MCP** (15 min)
2. **Arkitektur Oversikt** (15 min)
3. **Hands-on: Utforske Koden** (20 min)
4. **Bygging av Verktøy** (30 min)
5. **Deployment & Testing** (20 min)
6. **Avanserte Funksjoner** (20 min)
7. **Spørsmål & Neste Steg** (10 min)

---

<!-- _class: lead -->
# 🧠 Hva er Model Context Protocol?

---

# Model Context Protocol (MCP)

## Problemet
- AI modeller er kraftige men **isolerte**
- Trenger tilgang til **sanntidsdata**
- Ønsker å **utføre handlinger** i verden
- Sikkerhet og **standardisering** utfordringer

## Løsningen: MCP
- **Standardisert protokoll** for AI-verktøy integrasjon
- **Sikker** og **strukturert** kommunikasjon
- **Utvidbar** arkitektur for alle verktøy

---

# MCP Fordeler

## For utviklere
- 🔧 **Standardisert verktøy-grensesnitt**
- 🛡️ **Innebygde sikkerhetsmønstre**
- 📈 **Skalerbar arkitektur**
- 🔄 **Gjenbrukbare komponenter**

## For AI agenter
- 🌐 **Tilgang til eksterne APIer**
- 💾 **Sanntids data-henting**
- ⚡ **Handlingsutførelse muligheter**
- 🧠 **Forbedret resonnering med kontekst**

---

<!-- _class: lead -->
# 🏗️ Oversikt arkitektur

---

# Systemarkitektur

```
┌─────────────────┐    HTTP   ┌─────────────────┐    HTTP  ┌─────────────────┐
│   Web Frontend  │◄────────► │   AI Agent      │◄────────►│   MCP Server    │
│                 │           │                 │          │                 │
│  (HTML/JS)      │           │   (OpenAI)      │          │   (Verktøy)     │
└─────────────────┘           └─────────────────┘          └─────────────────┘
                                       │                            │
                                       │                            │
                                       ▼                            ▼
                              ┌─────────────────┐          ┌─────────────────┐
                              │ Samtale         │          │ Eksterne APIer  │
                              │ Minne (SQLite)  │          │ (OpenWeather)   │
                              └─────────────────┘          └─────────────────┘
```

---

# Komponenter

## 🖥️ **MCP Server**
- Eksponerer verktøy via HTTP API
- Håndterer ekstern API integrasjon

## 🤖 **AI Agent** 
- Prosesserer brukerforespørsler med OpenAI
- Kaller MCP verktøy når nødvendig

## 🌐 **Web Grensesnitt**
- Enkelt HTML frontend for testing
- Sanntids interaksjon med agent

---

# Dataflyt - Eksempel

## Bruker spør: *"Hva er været i Oslo?"*

1. **Web** → **Agent**: Brukerforespørsel
2. **Agent** → **OpenAI**: "Bruker vil ha vær for Oslo"
3. **OpenAI** → **Agent**: "Bruk get_weather_forecast verktøy"
4. **Agent** → **MCP Server**: Verktøykall med parametere
5. **MCP Server** → **OpenWeather API**: Hent værdata
6. **MCP Server** → **Agent**: Vær respons
7. **Agent** → **OpenAI**: "Formater denne værdataen"
8. **Agent** → **Web**: Formatert svar til bruker

---

<!-- _class: lead -->
# 🛠️ Hands-on: Utforske koden

---

# Prosjektstruktur

```
agent/
├── docker-compose.yml          # 🐳 Container orkestrering
├── .env.example               # 🔐 Miljøvariabler
├── services/
│   ├── mcp-server/            # 🔧 Verktøy server
│   │   └── app.py            # ⭐ Hoved server logikk
│   ├── agent/                 # 🤖 AI agent
│   │   ├── app.py            # ⭐ Agent implementasjon
│   │   └── conversation_memory.py
│   └── web/                   # 🌐 Frontend
└── logs/                      # 📝 Delt logging
```

---

# MCP Server - Kodegjennomgang

```python
@app.post("/tools/get_weather_forecast")
async def get_weather_forecast(request: WeatherRequest):
    """Hent værvarsel for en lokasjon."""
    try:
        # 1. Konverter lokasjon til koordinater
        coords = await geocode_location(request.location)
        
        # 2. Hent værdata fra OpenWeatherMap
        weather_data = await fetch_weather_data(coords)
        
        # 3. Returner strukturert respons
        return {
            "success": True,
            "location": request.location,
            "forecast": weather_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

# Agent - Kodegjennomgang

```python
# services/agent/app.py

# Verktøydefinisjon for OpenAI
self.tools = [{
    "type": "function",
    "function": {
        "name": "get_weather_forecast",
        "description": "Hent værvarsel for en lokasjon",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "days": {"type": "integer", "default": 3}
            },
            "required": ["location"]
        }
    }
}]
```

---

# Flyt - Verktøykall

```python
# Når OpenAI vil bruke et verktøy
if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        # Kall MCP server
        tool_result = await self.call_mcp_tool(tool_name, tool_args)
        
        # Legg til resultat i samtalen
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })
```

---

<!-- _class: lead -->
# 🔧 Hands-on: Bygging av verktøy

---

# Labøvelse 1: Utforsk nåværende verktøy

## La oss undersøke værverktøyet

```bash
# Start systemet
docker-compose up -d

# Test MCP server direkte
curl -X POST "http://localhost:8000/tools/get_weather_forecast" \
  -H "Content-Type: application/json" \
  -d '{"location": "Oslo", "days": 3}'

# Test via agent
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hva er været i Bergen?"}'
```

---

# Labøvelse 2: Legg til nytt verktøy

## La oss lage et "Tilfeldig Fakta" verktøy

### Steg 1: Legg til i MCP Server

```python
# I services/mcp-server/app.py

class FactRequest(BaseModel):
    category: str = "general"

@app.post("/tools/get_random_fact")
async def get_random_fact(request: FactRequest):
    """Få et tilfeldig interessant faktum."""
    facts = {
        "general": ["Honningbien produserer mat spist av mennesker.",
                   "Bananer er bær, men jordbær er ikke det."],
        "space": ["En dag på Venus er lengre enn året sitt.",
                 "Saturn ville flyte i vann."]
    }
    
    import random
    fact = random.choice(facts.get(request.category, facts["general"]))
    
    return {"success": True, "category": request.category, "fact": fact}
```

---

# Labøvelse 2: Registrer verktøy i agent

### Steg 2: Legg til i Agentverktøy Array

```python
# I services/agent/app.py, legg til i self.tools:

{
    "type": "function",
    "function": {
        "name": "get_random_fact",
        "description": "Få et tilfeldig interessant faktum",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Faktakategori (general, space)",
                    "default": "general"
                }
            }
        }
    }
}
```

---

# Labøvelse 2: Test det nye verktøyet

```bash
# Bygg på nytt og start
docker-compose build travel-agent mcp-server
docker-compose up -d

# Test det nye verktøyet
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Fortell meg et interessant faktum om verdensrommet"}'
```

## Forventet resultat
Agenten skal kalle ditt nye verktøy og returnere et romfaktum!

---

# Labøvelse 3: Ekte API integrasjon

## La oss legge til et ekte Nyhets API verktøy

```python
# I services/mcp-server/app.py

import httpx

class NewsRequest(BaseModel):
    topic: str
    language: str = "no"

@app.post("/tools/get_news")
async def get_news(request: NewsRequest):
    """Få nylige nyheter om et emne."""
    api_key = os.getenv("NEWS_API_KEY")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": request.topic,
                "language": request.language,
                "apiKey": api_key
            }
        )
    news_data = response.json()
    articles = [
        {"title": article["title"], "url": article["url"]}
        for article in news_data.get("articles", [])[:3]
    ]
    
    return {"success": True, "topic": request.topic, "articles": articles}
```

---

<!-- _class: lead -->
# 🐳 Deployment & Test

---

# Docker compose kommandoer

## Utviklingsarbeidsflyt

```bash
# Start fra bunnen av
docker-compose up --build

# Stopp alt
docker-compose down

# Bygg spesifikk tjeneste på nytt
docker-compose build mcp-server

# Se logger
docker-compose logs -f travel-agent

# Sjekk helse
curl http://localhost:8000/health
```

---

# Miljøoppsett

## 1. Kopier miljøfil
```bash
cp .env.example .env
```

## 2. Legg til API nøkler
```bash
# .env
OPENAI_API_KEY=your-openai-api-key-here
OPENWEATHER_API_KEY=your-openweather-api-key-here
NEWS_API_KEY=your-news-api-key-here  # Hvis du bruker news verktøy
```

## 3. Bygg og start
```bash
docker-compose up --build
```

---

# Teststrategi

## 1. Enhetstesting (Individuelle verktøy)
```bash
# Test MCP server endepunkter direkte
curl -X POST "http://localhost:8000/tools/get_weather_forecast" \
  -H "Content-Type: application/json" \
  -d '{"location": "Oslo"}'
```

## 2. Integrasjonstesting (Full flyt)
```bash
# Test gjennom agent
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hva er været i dag?"}'
```

## 3. Webtesting
Åpne http://localhost:3000 i nettleser

---

# Tips - Debugging

## Vanlige problemer & løsninger

### 🔴 **Container vil ikke starte**
```bash
docker-compose logs service-name
```

### 🔴 **API kall feiler**
```bash
docker-compose exec travel-agent env | grep API
```

### 🔴 **Verktøy ikke gjenkjent**
```bash
curl http://localhost:8001/health
```

---

<!-- _class: lead -->
# 🚀 Avanserte Funksjoner

---

# Avanserte verktøy - vanlige mønstre

## 1. **Verktøy med tilstand**
- Oppretthold kontekst mellom kall
- Brukerpreferanser og historie
- Sesjonshåndtering

## 2. **Asynkrone operasjoner**
- Langvarige oppgaver
- Bakgrunnsprosessering
- Fremdriftssporing

## 3. **Flertrinns arbeidsflyt**
- Verktøy-kjeding
- Betinget logikk
- Feilhåndtering og retry

---

# Sikkerhetsbetraktninger

## Inputvalidering
```python
from pydantic import BaseModel, validator

class SecureRequest(BaseModel):
    location: str
    
    @validator('location')
    def validate_location(cls, v):
        if len(v) > 100:
            raise ValueError('Lokasjon for lang')
        # Legg til mer validering...
        return v
```

## Håndtering - API nøkler 
```python
import os

def get_api_key(service: str) -> str:
    key = os.getenv(f"{service.upper()}_API_KEY")
    if not key:
        raise ValueError(f"Mangler {service} API nøkkel")
    return key
```

---

# Deployment - Produksjon

## Skalerbarhet
- **Lastbalansering** med flere agent instanser
- **Database clustering** for samtale minne
- **Caching** for ofte brukte verktøy resultater

## Overvåkning
- **Helse sjekker** og oppetid overvåkning
- **Logging aggregering** (ELK stack)
- **Metrics innsamling** (Prometheus/Grafana)
- **Feilsporing** (Sentry)

## Sikkerhet
- **API rate limiting**
- **Input sanitisering**
- **HTTPS terminering**
- **Håndtering av hemmeligheter**

---

# Utvidelse av arkitektur

## Legg til nye funksjoner

### 🧠 **Minne**
- Vektor databaser for semantisk søk
- Kunnskaps grafer for relasjoner
- Langsiktig læring og tilpasning

### 🔗 **Integrasjon**
- Webhook endepunkter for sanntid oppdateringer
- Meldingskøer for asynkron prosessering
- Hendelsesdrevet arkitektur

### 🌐 **Multi-Modal atøtte**
- Bildeanalyse verktøy
- Lydprosessering
- Tolking av video

---

<!-- _class: lead -->
# 💡 Workshop Øvelser

---

# Øvelse 1: Værforbedring
**Vanskelighet: Nybegynner**

Forbedre værverktøyet til å inkludere:
- UV-indeks informasjon
- Luftkvalitet data
- Soloppgang/solnedgang tider

**Tips:** OpenWeatherMap API gir all denne dataen i responsen!

---

# Øvelse 2: Kalkulatorverktøy
**Vanskelighet: Nybegynner**

Lag et kalkulator verktøy som kan:
- Utføre grunnleggende matematiske operasjoner
- Håndtere komplekse uttrykk
- Vise steg-for-steg løsninger

```python
# Verktøy idé
@app.post("/tools/calculate")
async def calculate(request: CalculationRequest):
    # Din implementasjon her
    pass
```

---

# Øvelse 3: Minne-Aktivert Chat
**Vanskelighet: Mellomnivå**

Utvid agenten til å huske:
- Brukerpreferanser (favoritt byer, enheter)
- Tidligere samtaler
- Personaliserte anbefalinger

**Filer å modifisere:**
- `conversation_memory.py`
- Logikk for samtale med agent

---

# Øvelse 4: Orkestrering - Arbeidsflyt
**Vanskelighet: Avansert**

Lag en reiseplanlegging arbeidsflyt:
1. Få vær for destinasjon
2. Finn nærliggende attraksjoner
3. Sjekk kalender tilgjengelighet
4. Send e-post sammendrag

**Krever:** Flere API integrasjoner + arbeidsflyt logikk

---

<!-- _class: lead -->
# 🎓 Viktige Lærdommer

---

# Hva du har lært

## 🧠 **Konsepter**
- Model Context Protocol grunnleggende
- AI agent arkitektur mønstre
- Verktøy-basert AI system design

## 🛠️ **Ferdigheter**
- Bygge MCP-kompatible verktøy
- Integrere eksterne APIer sikkert
- Docker containerisering for AI systemer

## 🚀 **Beste praksis**
- Strukturert feilhåndtering
- Sikkerhetsbetraktninger
- Testing strategier

---

# Neste Steg

## 📚 **Fortsett å lære**
- Utforsk MCP spesifikasjonen i dybden
- Studer avanserte AI agent mønstre
- Lær om vektor databaser og RAG

## 🔧 **Bygg mer**
- Lag industri-spesifikke verktøy
- Implementer produksjon overvåkning
- Skaler til multi-tenant arkitektur

## 🌐 **Community**
- Bli med i MCP utvikler community
- Bidra til open source verktøy
- Del dine implementasjoner

---

# Ressurser

## 📖 **Dokumentasjon**
- [Model Context Protocol Docs](https://modelcontextprotocol.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Docker Compose Guide](https://docs.docker.com/compose/)

## 🛠️ **Verktøy & Biblioteker**
- [FastAPI Dokumentasjon](https://fastapi.tiangolo.com/)
- [Pydantic for Data Validering](https://pydantic-docs.helpmanual.io/)
- [HTTPX for Async HTTP](https://www.python-httpx.org/)

## 💻 **Kildekode**
- Workshop repository: `github.com/your-repo/agent-workshop`
- Eksempel implementasjoner
- Utvidet verktøy bibliotek

---

<!-- _class: lead -->
# 🙋‍♂️ Spørsmål & diskusjon

## Takk for deltakelsen!

**Lars Søraas**  
📧 lsoraas@gmail.com  
🐙 github.com/zral  

---

<!-- _class: lead -->
# 🚀 Lykke til videre!

## Gå ut og lag fantastiske AI agenter!

### Husk:
- Start enkelt, iterer raskt
- Sikkerhet først, alltid
- Dokumentasjon er din venn
- Community er her for å hjelpe

**Måtte dine agenter være intelligente og dine verktøy være kraftige! 🤖✨**