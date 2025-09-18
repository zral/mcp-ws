#!/usr/bin/env python3
"""
Microservice Agent - AI Agent som kaller MCP Server via HTTP

Denne agenten kobler OpenAI GPT med MCP server som kjører som separat tjeneste.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

import httpx
from openai import OpenAI
from conversation_memory import ConversationMemory

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance for API server
agent_instance = None

class MicroserviceAgent:
    """
    AI Agent som bruker MCP server via HTTP API.
    
    Denne agenten:
    1. Håndterer OpenAI API kommunikasjon
    2. Kaller MCP server endpoints i stedet for direkte funksjoner
    3. Administrerer samtalehukommelse
    """
    
    def __init__(self, mcp_server_url: str = None, memory_db_path: str = "/data/conversations.db"):
        # Initialiser OpenAI klient
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url="https://models.github.ai/inference")
        
        # MCP server URL - bruk environment variable hvis tilgjengelig
        if mcp_server_url is None:
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")
        self.mcp_server_url = mcp_server_url
        
        # Initialiser hukommelse
        self.memory = ConversationMemory(memory_db_path)
        self.current_session_id = None
        
        # HTTP klient for MCP kall
        self.http_client = httpx.AsyncClient()
        
        # Tools vil bli hentet dynamisk fra MCP server
        self.tools = []
        # Tool endpoint mapping lagres separat
        self.tool_endpoints = {}
        
        logger.info("MicroserviceAgent initialisert")
    
    async def load_tools_from_mcp_server(self):
        """
        Hent tilgjengelige tools fra MCP server dynamisk.
        Konverterer fra MCP format til OpenAI function calling format og lagrer endpoint info.
        """
        try:
            logger.info(f"Henter tools fra MCP server: {self.mcp_server_url}")
            response = await self.http_client.get(f"{self.mcp_server_url}/tools")
            response.raise_for_status()
            
            mcp_tools = response.json()
            tools_list = mcp_tools.get("tools", [])
            
            # Konverter fra MCP format til OpenAI function calling format
            converted_tools = []
            tool_endpoints = {}
            
            for tool in tools_list:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["inputSchema"]
                    }
                }
                converted_tools.append(openai_tool)
                
                # Lagre endpoint-informasjon
                if "endpoint" in tool:
                    tool_endpoints[tool["name"]] = {
                        "endpoint": tool["endpoint"],
                        "method": tool.get("method", "POST")
                    }
            
            self.tools = converted_tools
            self.tool_endpoints = tool_endpoints
            logger.info(f"Lastet {len(self.tools)} tools fra MCP server med {len(self.tool_endpoints)} endpoint mappings")
            return True
            
        except Exception as e:
            logger.error(f"Kunne ikke hente tools fra MCP server: {e}")
            return False
    
    def _map_tool_to_endpoint(self, tool_name: str) -> str:
        """
        Map tool name to MCP server endpoint based on convention.
        Dette unngår hardkoding av endpoints i agent-koden.
        """
        # Konvensjon: get_weather_forecast -> /weather
        # Konvensjon: get_random_fact -> /fact
        # Konvensjon: get_news -> /news
        tool_to_endpoint = {
            "get_weather_forecast": "/weather",
            "get_random_fact": "/fact",
            "get_news": "/news"
        }
        
        # Standard fallback: remove 'get_' prefix if present
        if tool_name in tool_to_endpoint:
            return tool_to_endpoint[tool_name]
        
        # Fallback: derive endpoint from tool name
        if tool_name.startswith("get_"):
            endpoint_name = tool_name[4:]  # Remove 'get_' prefix
            return f"/{endpoint_name}"
        
        # Last resort: use tool name as-is
        return f"/{tool_name}"
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Kall MCP server via HTTP basert på endpoint info fra tools manifest.
        Bruker eksplisitt endpoint-mapping hvis tilgjengelig, ellers fallback til konvensjon.
        """
        try:
            logger.info(f"Kaller MCP server: {tool_name} med args: {arguments}")
            
            # Først: bruk eksplisitt endpoint info fra tools manifest
            if tool_name in self.tool_endpoints:
                endpoint_info = self.tool_endpoints[tool_name]
                endpoint = endpoint_info["endpoint"]
                method = endpoint_info.get("method", "POST")
                logger.info(f"Bruker eksplisitt endpoint mapping: {tool_name} -> {method} {endpoint}")
            else:
                # Fallback: bruk konvensjonbasert mapping
                endpoint = self._map_tool_to_endpoint(tool_name)
                method = "POST"
                logger.warning(f"Ingen eksplisitt endpoint for {tool_name}, bruker fallback: {endpoint}")
            
            # Gjør HTTP kall til MCP server
            url = f"{self.mcp_server_url}{endpoint}"
            
            # Støtt forskjellige HTTP metoder
            if method.upper() == "GET":
                response = await self.http_client.get(url, params=arguments)
            elif method.upper() == "POST":
                response = await self.http_client.post(url, json=arguments)
            elif method.upper() == "PUT":
                response = await self.http_client.put(url, json=arguments)
            elif method.upper() == "DELETE":
                response = await self.http_client.delete(url, params=arguments)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                return json.dumps(result["data"], ensure_ascii=False)
            else:
                return json.dumps({"error": result.get("error", "Unknown error")})
                
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return json.dumps({"error": str(e)})
    
    def start_new_session(self, session_name: str = None):
        """Start en ny samtalesession."""
        if not session_name:
            session_name = f"Microservice_Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session_id = self.memory.create_session(session_name)
        logger.info(f"Ny session startet: {self.current_session_id}")
    
    async def process_query(self, query: str) -> str:
        """
        Prosesser brukerforespørsel med AI og MCP verktøy.
        """
        if not self.current_session_id:
            self.start_new_session()
        
        try:
            # Hent samtalehistorikk
            history = self.memory.get_conversation_history(self.current_session_id)
            
            # Bygg meldinger for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """Du er Ingrid, en vennlig og kompetent værekspert fra Ingrids Reisetjenester. 

Dette er LAB01 versjonen - en forenklet utgave for workshop deltagere.

Du har kun tilgang til ett verktøy:
- get_weather_forecast: Hent værprognose for en destinasjon

Du skal fokusere på å hjelpe brukere med værinformasjon og gi praktiske råd basert på værforholdene.

Bruk verktøyet når brukere spør om vær for spesifikke steder. Gi alltid nyttige råd om klær, aktiviteter og forholdsregler basert på værmeldingen.

Vær vennlig, personlig og hjelpsom - du representerer Ingrids Reisetjenester.
Svar på norsk med mindre brukeren spør på et annet språk.

MERK: Dette er en forenklet versjon. Brukere kan spørre om andre tjenester, men du kan kun hjelpe med vær."""
                }
            ]
            
            # Legg til samtalehistorikk
            for msg in history:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    messages.append({"role": "assistant", "content": msg["content"]})
            
            # Legg til ny brukermelding
            messages.append({"role": "user", "content": query})
            
            # Første AI-kall med OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Håndter verktøykall
            if response_message.tool_calls:
                # Legg til assistant melding med tool calls
                messages.append({
                    "role": "assistant", 
                    "content": response_message.content,
                    "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in response_message.tool_calls]
                })
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Kall MCP server
                    tool_result = await self.call_mcp_tool(function_name, arguments)
                    
                    messages.append({
                        "role": "tool",
                        "content": tool_result,
                        "tool_call_id": tool_call.id
                    })
                
                logger.info("Verktøykall fullført, henter endelig svar...")
                
                # Få endelig svar med OpenAI
                final_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages
                )
                
                final_answer = final_response.choices[0].message.content
            else:
                final_answer = response_message.content
            
            # Lagre samtale
            self.memory.add_message(self.current_session_id, "user", query)
            self.memory.add_message(self.current_session_id, "assistant", final_answer)
            
            return final_answer
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return f"Beklager, jeg fikk en feil: {str(e)}"
    
    async def close(self):
        """Clean up ressurser."""
        await self.http_client.aclose()

# Test funksjon
async def main():
    """CLI interface for testing."""
    agent = MicroserviceAgent()
    
    # Last inn tools fra MCP server
    tools_loaded = await agent.load_tools_from_mcp_server()
    if not tools_loaded:
        logger.warning("Kunne ikke laste tools fra MCP server, fortsetter uten tools")
    
    agent.start_new_session("Test Session")
    
    while True:
        query = input("Du: ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        response = await agent.process_query(query)
        print(f"Ingrid: {response}\n")
    
    await agent.close()

def start_agent_api():
    """Start agent som HTTP API service."""
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from contextlib import asynccontextmanager
    import uvicorn
    
    # Global agent instance - definert på modul nivå
    global agent_instance
    agent_instance = None
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        global agent_instance
        logger.info("Starter Ingrid Agent Service...")
        try:
            agent_instance = MicroserviceAgent()
            
            # Last inn tools fra MCP server
            tools_loaded = await agent_instance.load_tools_from_mcp_server()
            if not tools_loaded:
                logger.warning("Kunne ikke laste tools fra MCP server, fortsetter uten tools")
            
            agent_instance.start_new_session("HTTP API Session")
            logger.info("Ingrid Agent Service startet")
            logger.info(f"Agent instance created: {agent_instance is not None}")
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            agent_instance = None
        
        yield
        
        # Shutdown
        if agent_instance:
            await agent_instance.close()
        logger.info("Ingrid Agent Service avsluttet")
    
    # FastAPI app for agent
    agent_app = FastAPI(
        title="Ingrid Agent API",
        description="AI agent service for Ingrids Reisetjenester",
        version="1.0.0",
        lifespan=lifespan
    )
    
    class QueryRequest(BaseModel):
        query: str
    
    class QueryResponse(BaseModel):
        success: bool
        response: str
        timestamp: str
    
    @agent_app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "Ingrid Agent",
            "timestamp": datetime.now().isoformat(),
            "agent_ready": agent_instance is not None
        }
    
    @agent_app.post("/query", response_model=QueryResponse)
    async def process_query_api(request: QueryRequest):
        global agent_instance
        logger.info(f"Query request received: {request.query}")
        logger.info(f"Agent instance status: {agent_instance is not None}")
        
        if not agent_instance:
            logger.error("Agent instance is None!")
            raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
        
        try:
            logger.info("Processing query with agent...")
            response = await agent_instance.process_query(request.query)
            logger.info("Query processed successfully")
            return QueryResponse(
                success=True,
                response=response,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Start HTTP server
    logger.info("Starting Agent API on port 8001...")
    uvicorn.run(agent_app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    logger.info("Starting Agent Service on port 8001...")
    start_agent_api()
