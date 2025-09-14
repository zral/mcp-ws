# MCP Agent Arkitektur & Template Guide

## Oversikt

Dette dokumentet forklarer i detalj hvordan Travel Weather MCP Agent er bygget opp, og fungerer som en mal for å lage nye MCP-baserte agenter. Arkitekturen skiller mellom **MCP Server** (verktøy/tools) og **Agent** (AI-logikk), med REST API som brukergrensesnitt.

## 🏗️ Systemarkitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        BRUKERGRENSESNITT                        │
├─────────────────────────────────────────────────────────────────┤
│  Web Browser          │  CLI Terminal        │  API Klienter    │
│  localhost:8080       │  python simple_agent │  HTTP requests   │
└─────────────────┬─────────────────┬─────────────────┬───────────┘
                  │                 │                 │
        ┌─────────▼─────────────────▼─────────────────▼───────────┐
        │                   REST API LAYER                       │
        │              web_agent.py (FastAPI)                    │
        └─────────────────────────┬─────────────────────────────┘
                                  │
        ┌─────────────────────────▼─────────────────────────────┐
        │                  AI AGENT LAYER                       │
        │           simple_agent.py (SimpleTravelWeatherAgent)  │
        │  ┌─────────────────┬──────────────────┬──────────────┐ │
        │  │  OpenAI GPT-4o  │  Function Calling │  Memory DB   │ │
        │  │  Conversation   │  Tool Selection   │  SQLite      │ │
        └──┴─────────────────┴──────────────────┴──────────────┴─┘
                                  │
        ┌─────────────────────────▼─────────────────────────────┐
        │                   MCP TOOLS LAYER                     │
        │               mcp_server.py (Functions)               │
        │  ┌──────────────┬─────────────────┬─────────────────┐ │
        │  │get_weather_  │get_travel_      │plan_trip        │ │
        │  │forecast      │routes           │                 │ │
        └──┴──────────────┴─────────────────┴─────────────────┴─┘
                                  │
        ┌─────────────────────────▼─────────────────────────────┐
        │                EXTERNAL APIs LAYER                    │
        │  ┌──────────────┬─────────────────┬─────────────────┐ │
        │  │OpenWeatherMap│ OpenRouteService│ Nominatim       │ │
        │  │(Weather API) │ (Routing API)   │ (Geocoding)     │ │
        └──┴──────────────┴─────────────────┴─────────────────┴─┘
```

## 📝 Komponentbeskrivelse

### 1. MCP Server Layer (`mcp_server.py`)

**Ansvar**: Implementerer rene verktøyfunksjoner uten AI-logikk.

```python
# mcp_server.py - Template struktur
import asyncio
import httpx
import logging
from typing import Dict, Any, Optional

# Global konfigurasjon
API_KEYS = {
    'service1': os.getenv('SERVICE1_API_KEY'),
    'service2': os.getenv('SERVICE2_API_KEY')
}

# Tool 1: Eksempel værfunksjon
async def get_weather_forecast(location: str, days: int = 5) -> Dict[str, Any]:
    """
    MCP Tool - Henter værprognose
    
    Dette er en ren funksjon som:
    1. Tar strukturerte parametere
    2. Kaller eksterne API-er
    3. Returnerer strukturert data
    4. Håndterer feil gracefully
    """
    try:
        # 1. Valider input
        if not location or not isinstance(location, str):
            raise ValueError("Location må være en ikke-tom string")
        
        days = max(1, min(days, 5))  # Begrens til 1-5 dager
        
        # 2. Geocoding - konverter navn til koordinater
        coordinates = await geocode_location(location)
        if not coordinates:
            return {"error": f"Kunne ikke finne lokasjon: {location}"}
        
        # 3. Kall værAPI
        weather_data = await fetch_weather_api(coordinates, days)
        
        # 4. Transformer data til standardisert format
        return {
            "location": location,
            "coordinates": coordinates,
            "forecast": transform_weather_data(weather_data),
            "status": "success"
        }
        
    except Exception as e:
        logging.error(f"Weather API feil: {e}")
        return {"error": str(e), "status": "failed"}

# Tool 2: Eksempel rutefunksjon  
async def get_travel_routes(origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
    """MCP Tool - Beregner reiseruter"""
    # Lignende struktur som over...
    pass

# Tool 3: Sammensatt funksjon
async def plan_trip(origin: str, destination: str, travel_date: str = None, 
                   mode: str = "driving", days: int = 5) -> Dict[str, Any]:
    """
    MCP Tool - Komplett reiseplanlegging
    
    Denne funksjonen kombinerer andre tools:
    """
    # Parallell henting av data
    weather_task = get_weather_forecast(destination, days)
    route_task = get_travel_routes(origin, destination, mode)
    
    weather, route = await asyncio.gather(weather_task, route_task)
    
    return {
        "trip_plan": {
            "route": route,
            "weather": weather,
            "recommendations": generate_travel_advice(route, weather)
        }
    }

# Hjelpefunksjoner
async def geocode_location(location: str) -> Optional[tuple]:
    """Konverter stedsnavn til koordinater"""
    # Implementasjon...

async def fetch_weather_api(coordinates: tuple, days: int) -> Dict:
    """Hent værdata fra ekstern API"""
    # Implementasjon...

def transform_weather_data(raw_data: Dict) -> List[Dict]:
    """Transform API data til standardisert format"""
    # Implementasjon...
```

**🔑 MCP Server Prinsipper:**
- **Rene funksjoner**: Ingen AI-logikk, kun datahenting
- **Async/await**: Alle funksjoner er asynkrone for ytelse
- **Strukturert I/O**: Klare input parametere og output format
- **Feilhåndtering**: Robust error handling med fallbacks
- **Modulært**: Hver funksjon har ett ansvarsområde

### 2. AI Agent Layer (`simple_agent.py`)

**Ansvar**: Kobler AI (OpenAI GPT) med MCP verktøy.

```python
# simple_agent.py - Template struktur
import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
from conversation_memory import ConversationMemory
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip

class SimpleTravelWeatherAgent:
    """
    AI Agent som bruker MCP tools via direkte import.
    
    Denne klassen:
    1. Håndterer OpenAI API kommunikasjon
    2. Definerer tilgjengelige verktøy for AI
    3. Utfører verktøykall basert på AI-beslutninger
    4. Håndterer samtalehukommelse
    """
    
    def __init__(self, memory_db_path: str = "/data/conversations.db"):
        # 1. Initialiser AI klient
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 2. Initialiser hukommelse
        self.memory = ConversationMemory(memory_db_path)
        self.current_session_id = None
        
        # 3. Definer verktøy for OpenAI Function Calling
        self.tools = self._define_tools()
    
    def _define_tools(self) -> List[Dict]:
        """
        Definer verktøy som OpenAI kan bruke.
        
        Dette er mappingen mellom OpenAI Function Calling og MCP tools.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_weather_forecast",
                    "description": "Hent værprognose for en destinasjon",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Navn på by eller lokasjon"
                            },
                            "days": {
                                "type": "integer", 
                                "description": "Antall dager fremover (1-5)",
                                "default": 5
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            # Legg til flere verktøy her...
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Utfør MCP verktøykall basert på AI-beslutning.
        
        Dette er bindeleddet mellom OpenAI og MCP tools.
        """
        try:
            logging.info(f"Utfører verktøykall: {tool_name} med args: {arguments}")
            
            # Map tool name til MCP funksjon
            if tool_name == "get_weather_forecast":
                result = await get_weather_forecast(**arguments)
            elif tool_name == "get_travel_routes":
                result = await get_travel_routes(**arguments)
            elif tool_name == "plan_trip":
                result = await plan_trip(**arguments)
            else:
                raise ValueError(f"Ukjent verktøy: {tool_name}")
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logging.error(f"Verktøykall feilet: {e}")
            return json.dumps({"error": str(e)})
    
    async def process_query(self, query: str) -> str:
        """
        Hovedfunksjon - prosesser brukerforespørsel med AI og verktøy.
        
        Flow:
        1. Send query til OpenAI med tilgjengelige verktøy
        2. Hvis AI vil bruke verktøy, utfør dem
        3. Send resultater tilbake til AI for endelig svar
        4. Lagre samtale i hukommelse
        """
        # 1. Bygg samtalehistorikk
        messages = self._build_conversation_context()
        messages.append({"role": "user", "content": query})
        
        # 2. Første AI-kall med verktøytilgang
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"  # La AI bestemme om den vil bruke verktøy
        )
        
        response_message = response.choices[0].message
        
        # 3. Håndter verktøykall hvis AI ønsker det
        if response_message.tool_calls:
            # Utfør alle verktøykall
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Kall MCP verktøy
                tool_result = await self.call_tool(function_name, arguments)
                
                # Legg til resultat i samtale
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # 4. Få endelig svar fra AI
            final_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            
            final_answer = final_response.choices[0].message.content
        else:
            final_answer = response_message.content
        
        # 5. Lagre samtale
        self._save_conversation(query, final_answer)
        
        return final_answer
    
    def _build_conversation_context(self) -> List[Dict]:
        """Bygg samtalehistorikk fra hukommelse"""
        # Implementasjon...
    
    def _save_conversation(self, query: str, response: str):
        """Lagre samtale i database"""
        # Implementasjon...
```

**🔑 Agent Prinsipper:**
- **AI Orchestration**: Lar AI bestemme hvilke verktøy som skal brukes
- **Function Calling**: Bruker OpenAI sin native verktøystøtte
- **Memory Management**: Persistent samtalehukommelse
- **Error Resilience**: Robust håndtering av både AI og tool feil

### 3. REST API Layer (`web_agent.py`)

**Ansvar**: HTTP grensesnitt for agenten.

```python
# web_agent.py - Template struktur
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from simple_agent import SimpleTravelWeatherAgent

# FastAPI app setup
app = FastAPI(
    title="Travel Weather Agent API",
    description="REST API for Travel Weather AI Agent",
    version="1.0.0"
)

# Global agent instance
agent_instance: SimpleTravelWeatherAgent = None
templates = Jinja2Templates(directory="templates")

# Request/Response modeller
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    response: str
    timestamp: str
    agent_connected: bool

# API Endpoints
@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Hovedendpoint - prosesser brukerforespørsel
    
    Dette endepunktet:
    1. Tar imot brukerforespørsel via HTTP
    2. Sender til AI agent for prosessering  
    3. Returnerer strukturert svar
    """
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        # Prosesser med AI agent
        response = await agent_instance.process_query(request.query)
        
        return QueryResponse(
            success=True,
            response=response,
            timestamp=datetime.now().isoformat(),
            agent_connected=True
        )
        
    except Exception as e:
        logging.error(f"Query prosessering feilet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_available": agent_instance is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Web UI for testing"""
    return templates.TemplateResponse("index.html", {"request": request})

# Lifecycle management
@app.on_event("startup")
async def startup_event():
    """Initialiser agent ved oppstart"""
    global agent_instance
    try:
        agent_instance = SimpleTravelWeatherAgent()
        agent_instance.start_new_session("Web Interface Session")
        logging.info("Agent startet successfully")
    except Exception as e:
        logging.error(f"Agent startup feilet: {e}")
        agent_instance = None

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup ved nedstengning"""
    global agent_instance
    if agent_instance:
        # Cleanup logic her
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**🔑 REST API Prinsipper:**
- **Separation of Concerns**: API håndterer kun HTTP, ikke AI-logikk
- **Standardiserte responses**: Konsistent JSON struktur
- **Health checks**: Monitoring endpoints
- **Error handling**: Proper HTTP statuskoder

## 🛠️ Template for ny MCP Agent

### Steg 1: Definer domenet ditt

```python
# Eksempel: E-commerce Price Agent
# mcp_server.py

async def get_product_prices(product_name: str, stores: List[str]) -> Dict[str, Any]:
    """MCP Tool - Hent produktpriser fra flere butikker"""
    pass

async def check_stock_availability(product_id: str, store: str) -> Dict[str, Any]:
    """MCP Tool - Sjekk lagerstatus"""
    pass

async def compare_deals(product_category: str, budget: float) -> Dict[str, Any]:
    """MCP Tool - Sammenlign tilbud"""
    pass
```

### Steg 2: Lag din Agent

```python
# simple_agent.py
class SimpleEcommerceAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.tools = [
            # Definer dine verktøy her...
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict):
        if tool_name == "get_product_prices":
            return await get_product_prices(**arguments)
        # Håndter andre verktøy...
```

### Steg 3: Lag REST API

```python
# web_agent.py  
from simple_agent import SimpleEcommerceAgent

app = FastAPI(title="E-commerce Agent API")
agent_instance: SimpleEcommerceAgent = None

@app.post("/query")
async def process_query(request: QueryRequest):
    response = await agent_instance.process_query(request.query)
    return {"response": response}
```

### Steg 4: Docker deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "web_agent.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  ecommerce-agent:
    build: .
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - STORE_API_KEY=${STORE_API_KEY}
```

## 🔄 Data Flow

### Typisk forespørsel flow:

```
1. HTTP Request → web_agent.py
   POST /query {"query": "Finn billigste pris på iPhone"}

2. web_agent.py → simple_agent.py  
   agent.process_query("Finn billigste pris på iPhone")

3. simple_agent.py → OpenAI API
   Chat completion med tools=[get_product_prices, ...]

4. OpenAI → simple_agent.py
   Response: "Kall get_product_prices(product='iPhone')"

5. simple_agent.py → mcp_server.py
   await get_product_prices(product="iPhone")

6. mcp_server.py → Eksterne API-er
   API calls til Amazon, Elkjøp, etc.

7. Eksterne API-er → mcp_server.py
   Prisdata tilbake

8. mcp_server.py → simple_agent.py
   Strukturert prisdata

9. simple_agent.py → OpenAI API  
   "Her er prisdataene, lag et svar til brukeren"

10. OpenAI → simple_agent.py
    "iPhone koster fra 8990 kr hos Elkjøp..."

11. simple_agent.py → web_agent.py
    Final response string

12. web_agent.py → HTTP Response
    {"response": "iPhone koster fra 8990 kr..."}
```

## 📊 Sammenligning: MCP vs Tradisjonelle tilnærminger

| Aspekt | MCP Approach | Tradisjonell Approach |
|--------|--------------|----------------------|
| **Verktøy definisjon** | Rene async funksjoner | Classes, methods, frameworks |
| **AI integrasjon** | OpenAI Function Calling | Custom parsing/routing |
| **Feilhåndtering** | Per-tool error handling | Monolittisk error handling |
| **Testing** | Enkle unit tests | Complex mocking |
| **Skalering** | Parallelle async kall | Sequential execution |
| **Vedlikehold** | Modulært, løs kobling | Tett kobling |

## 🚀 Best Practices

### 1. MCP Tool Design
```python
# ✅ GOOD: Ren, fokusert funksjon
async def get_weather(location: str, days: int = 5) -> Dict[str, Any]:
    # Single responsibility
    # Clear input/output
    # Async for performance
    pass

# ❌ BAD: Blandet ansvar  
async def get_weather_and_send_email(location: str, email: str):
    # Gjør for mye
    # Vanskelig å teste
    # Ikke gjenbrukbar
    pass
```

### 2. Error Handling
```python
# ✅ GOOD: Graceful degradation
async def get_route_with_fallback(origin: str, destination: str):
    try:
        return await openroute_api_call(origin, destination)
    except Exception:
        logger.warning("Primary API failed, using fallback")
        return calculate_air_distance(origin, destination)

# ❌ BAD: Fail fast
async def get_route_strict(origin: str, destination: str):
    return await openroute_api_call(origin, destination)  # Kan feile
```

### 3. Agent Configuration
```python
# ✅ GOOD: Konfigurerbar agent
class MyAgent:
    def __init__(self, model="gpt-4o", max_tools=5):
        self.model = model
        self.max_tools = max_tools
        
# ❌ BAD: Hardkodet verdier
class MyAgent:
    def __init__(self):
        self.model = "gpt-4o"  # Ikke konfigurerbar
```

## 🎯 Bruksområder for MCP Agents

Denne arkitekturen passer godt til:

- **Datainnhenting**: Værdata, aksjekurser, nyheter
- **API integrasjon**: Kombinere flere tjenester
- **Sammenligning**: Priser, tjenester, alternativer  
- **Planlegging**: Reiser, events, ressurser
- **Analyse**: Trender, mønstre, insights

## 💡 Utvidelsesmuligheter

- **Caching**: Redis for å cache API-resultater
- **Rate limiting**: Respekter API-grenser
- **Monitoring**: Prometheus/Grafana for metrics
- **Security**: API keys, authentication
- **Scaling**: Kubernetes deployment
- **Multi-tenant**: Støtte for flere brukere

Denne arkitekturen gir deg en solid base for å bygge kraftige, skalerbare AI-agenter med MCP verktøy!
