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
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # MCP server URL - bruk environment variable hvis tilgjengelig
        if mcp_server_url is None:
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000")
        self.mcp_server_url = mcp_server_url
        
        # Initialiser hukommelse
        self.memory = ConversationMemory(memory_db_path)
        self.current_session_id = None
        
        # HTTP klient for MCP kall
        self.http_client = httpx.AsyncClient()
        
        # Definer verktøy for OpenAI
        self.tools = [
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
            {
                "type": "function", 
                "function": {
                    "name": "get_travel_routes",
                    "description": "Hent reiseruter mellom to destinasjoner",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Start destinasjon"
                            },
                            "destination": {
                                "type": "string", 
                                "description": "Slutt destinasjon"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Transportmåte: driving, walking, cycling",
                                "default": "driving"
                            }
                        },
                        "required": ["origin", "destination"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "plan_trip", 
                    "description": "Lag komplett reiseplan med vær og rute",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Start destinasjon"
                            },
                            "destination": {
                                "type": "string",
                                "description": "Slutt destinasjon"
                            },
                            "travel_date": {
                                "type": "string",
                                "description": "Reisedato (valgfritt)"
                            },
                            "mode": {
                                "type": "string", 
                                "description": "Transportmåte",
                                "default": "driving"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Antall dager værprognose",
                                "default": 5
                            }
                        },
                        "required": ["origin", "destination"]
                    }
                }
            }
        ]
        
        logger.info("MicroserviceAgent initialisert")
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Kall MCP server via HTTP i stedet for direkte funksjoner.
        """
        try:
            logger.info(f"Kaller MCP server: {tool_name} med args: {arguments}")
            
            # Map tool name til MCP endpoint
            if tool_name == "get_weather_forecast":
                endpoint = "/weather"
                payload = {
                    "location": arguments["location"],
                    "days": arguments.get("days", 5)
                }
            elif tool_name == "get_travel_routes":
                endpoint = "/routes"
                payload = {
                    "origin": arguments["origin"],
                    "destination": arguments["destination"], 
                    "mode": arguments.get("mode", "driving")
                }
            elif tool_name == "plan_trip":
                endpoint = "/plan"
                payload = {
                    "origin": arguments["origin"],
                    "destination": arguments["destination"],
                    "travel_date": arguments.get("travel_date"),
                    "mode": arguments.get("mode", "driving"),
                    "days": arguments.get("days", 5)
                }
            else:
                raise ValueError(f"Ukjent verktøy: {tool_name}")
            
            # Gjør HTTP kall til MCP server
            url = f"{self.mcp_server_url}{endpoint}"
            response = await self.http_client.post(url, json=payload)
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
                    "content": """Du er Ingrid, en vennlig og kompetent reiseassistent fra Ingrids Reisetjenester. Du hjelper brukere med smart reiseplanlegging basert på værutsikter og optimale ruter.

Du har tilgang til disse verktøyene:
- get_weather_forecast: Hent værprognose for en destinasjon
- get_travel_routes: Hent reiseruter mellom to destinasjoner  
- plan_trip: Lag komplett reiseplan med vær og rute

Du skal kun svare på reise- og vær-relaterte spørsmål. Du er ekspert på reiseplanlegging og gir alltid praktiske råd.

Bruk verktøyene når det trengs for å gi nyttige og nøyaktige svar. Vær vennlig, personlig og hjelpsom - du representerer Ingrids Reisetjenester.
Svar på norsk med mindre brukeren spør på et annet språk."""
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
            
            # Første AI-kall
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Håndter verktøykall
            if response_message.tool_calls:
                messages.append(response_message)
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Kall MCP server
                    tool_result = await self.call_mcp_tool(function_name, arguments)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                logger.info("Verktøykall fullført, henter endelig svar...")
                
                # Få endelig svar
                final_response = self.client.chat.completions.create(
                    model="gpt-4o",
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
    import uvicorn
    
    # FastAPI app for agent
    agent_app = FastAPI(
        title="Ingrid Agent API",
        description="AI agent service for Ingrids Reisetjenester",
        version="1.0.0"
    )
    
    # Global agent instance - definert på modul nivå
    global agent_instance
    agent_instance = None
    
    class QueryRequest(BaseModel):
        query: str
    
    class QueryResponse(BaseModel):
        success: bool
        response: str
        timestamp: str
    
    @agent_app.on_event("startup")
    async def startup():
        global agent_instance
        logger.info("Starter Ingrid Agent Service...")
        try:
            agent_instance = MicroserviceAgent()
            agent_instance.start_new_session("HTTP API Session")
            logger.info("Ingrid Agent Service startet")
            logger.info(f"Agent instance created: {agent_instance is not None}")
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            agent_instance = None
    
    @agent_app.on_event("shutdown") 
    async def shutdown():
        global agent_instance
        if agent_instance:
            await agent_instance.close()
        logger.info("Ingrid Agent Service avsluttet")
    
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
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        start_agent_api()
    else:
        asyncio.run(main())
