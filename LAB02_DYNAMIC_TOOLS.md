# LAB02 Dynamic Tools Discovery - Hardkoding Fjernet

## Problem Løst i LAB02 Branch

### ❌ Før: Hardkodet Endpoint Mapping
```python
def _map_tool_to_endpoint(self, tool_name: str) -> str:
    # PROBLEMATISK HARDKODING
    tool_to_endpoint = {
        "get_weather_forecast": "/weather",
        "get_random_fact": "/fact", 
        "get_news": "/news"
    }
    
    if tool_name in tool_to_endpoint:
        return tool_to_endpoint[tool_name]  # Hardkodet!
```

**Problemer:**
- 🚫 Hardkodet endpoint mappings
- 🚫 MCP server kan ikke definere egne endpoints
- 🚫 Ikke skalerbart for nye tools
- 🚫 Bryter MCP protokoll prinsippet om dynamisk discovery

### ✅ Etter: Dynamisk Endpoint Discovery
```python
def _map_tool_to_endpoint(self, tool_name: str) -> str:
    """
    WARNING: This is a fallback mechanism. The MCP server should 
    provide explicit endpoint mappings via the tools endpoint.
    """
    logger.warning(f"Using fallback endpoint mapping for tool: {tool_name}")
    logger.warning("Consider updating MCP server to provide explicit endpoint mappings")
    
    # Kun konvensjonsbasert fallback - ingen hardkoding
    if tool_name.startswith("get_"):
        endpoint_name = tool_name[4:]
        return f"/{endpoint_name.replace('_', '-')}"
    
    return f"/{tool_name.replace('_', '-')}"
```

**Forbedringer:**
- ✅ Ingen hardkoding av endpoint mappings
- ✅ Prioriterer dynamiske mappings fra MCP server
- ✅ Proper warnings når fallback brukes  
- ✅ REST conventions (underscores → hyphens)

## Prioritetsrekkefølge for Endpoint Discovery

### 1. **PRIORITET 1: MCP Server Endpoint Info** (Anbefalt)
```python
# Fra MCP server /tools endpoint
{
    "name": "get_weather_forecast",
    "endpoint": "/weather",
    "method": "POST"
}
```

### 2. **PRIORITET 2: Konvensjonsbasert Fallback** (Backup)
```python
# Automatisk mapping basert på tool navn
"get_weather_forecast" → "/weather-forecast"
"get_ping" → "/ping" 
"health_check" → "/health-check"
```

## Logging og Debugging

### Dynamisk Mapping (Ønsket):
```
INFO: Bruker dynamisk endpoint mapping fra MCP server: get_weather_forecast -> POST /weather
```

### Fallback Mapping (Warning):
```
WARNING: Ingen eksplisitt endpoint fra MCP server for get_weather_forecast, bruker fallback: /weather-forecast
WARNING: Consider updating MCP server to provide explicit endpoint mappings
```

## LAB02 vs LAB01 Forskjeller

| Aspekt | LAB01 (Workshop) | LAB02 (Advanced) |
|--------|------------------|------------------|
| **Tool Begrensning** | Kun første tool | Alle tools tilgjengelig |
| **Endpoint Mapping** | Dynamisk (ingen hardkoding) | Dynamisk (ingen hardkoding) |
| **Arkitektur** | Monolittisk (`app.py`) | Refaktorert tilgjengelig |
| **Kompleksitet** | Enkel for workshop | Full funksjonalitet |
| **Hardkoding** | Fjernet ✅ | Fjernet ✅ |

## Best Practices for MCP Server

### ✅ Anbefalt: Eksplisitt Endpoint Info
```json
{
    "tools": [
        {
            "name": "get_weather_forecast",
            "description": "Get weather forecast",
            "inputSchema": {...},
            "endpoint": "/weather",
            "method": "POST"
        },
        {
            "name": "get_server_status", 
            "description": "Get server status",
            "inputSchema": {...},
            "endpoint": "/status",
            "method": "GET"
        }
    ]
}
```

### ⚠️ Fallback: Kun Navn (Agent konverterer)
```json
{
    "tools": [
        {
            "name": "get_weather_forecast",
            "description": "Get weather forecast", 
            "inputSchema": {...}
            // Ingen endpoint info - agent bruker fallback
        }
    ]
}
```

## Resultater

✅ **Full Dynamisk Discovery**: Ingen hardkoding i agent  
✅ **MCP Protocol Compliant**: Server definerer sine egne endpoints  
✅ **Skalerbart**: Nye tools kan legges til uten agent endringer  
✅ **Proper Warnings**: Klare beskjeder når fallback brukes  
✅ **REST Conventions**: Konsistent endpoint naming  

**LAB02 demonstrerer nå fullstendig dynamisk tools discovery uten hardkoding!** 🎯