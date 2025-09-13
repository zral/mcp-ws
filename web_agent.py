"""
Web interface for Travel Weather Agent

En enkel web-basert grensesnitt for å bruke Travel Weather Agent
uten å måtte kjøre kommandoer direkte på host-maskinen.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

from agent import TravelWeatherAgent

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Travel Weather Agent Web Interface",
    description="Web interface for planning trips based on weather conditions",
    version="1.0.0"
)

# Templates og statiske filer
templates = Jinja2Templates(directory="templates")

# Global agent instans
agent_instance = None

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class SessionRequest(BaseModel):
    title: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agent_connected: bool

@app.on_event("startup")
async def startup_event():
    """Initialiser agent ved oppstart."""
    global agent_instance
    try:
        logger.info("Starter Travel Weather Agent...")
        agent_instance = TravelWeatherAgent()
        await agent_instance.connect_to_mcp_server()
        # Start en default web sesjon
        agent_instance.start_new_session("Web Interface Session")
        logger.info("Agent startet og tilkoblet MCP server")
    except Exception as e:
        logger.error(f"Feil ved oppstart av agent: {e}")
        agent_instance = None

@app.on_event("shutdown")
async def shutdown_event():
    """Avslutt agent ved nedstengning."""
    global agent_instance
    if agent_instance:
        await agent_instance.disconnect()
        logger.info("Agent avsluttet")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Hjem side med web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Helse sjekk for agent."""
    return HealthResponse(
        status="healthy" if agent_instance else "unhealthy",
        timestamp=datetime.now().isoformat(),
        agent_connected=agent_instance is not None
    )

@app.post("/query")
async def process_query(query_request: QueryRequest):
    """Prosesser en brukerforespørsel."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        response = await agent_instance.process_query(query_request.query)
        return JSONResponse(content={
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Feil ved prosessering av forespørsel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_available_tools():
    """Hent tilgjengelige verktøy fra MCP server."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        tools = []
        for tool in agent_instance.tools:
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            })
        
        return JSONResponse(content={
            "success": True,
            "tools": tools
        })
    except Exception as e:
        logger.error(f"Feil ved henting av verktøy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions")
async def create_session(request: SessionRequest):
    """Opprett ny samtalesesjon."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        session_id = agent_instance.start_new_session(request.title)
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "title": request.title or "Uten tittel"
        })
    except Exception as e:
        logger.error(f"Feil ved opprettelse av sesjon: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions")
async def list_sessions():
    """Hent liste over sesjoner."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        sessions = agent_instance.list_sessions()
        return JSONResponse(content={
            "success": True,
            "sessions": sessions
        })
    except Exception as e:
        logger.error(f"Feil ved henting av sesjoner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Hent samtalehistorikk for en sesjon."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        history = agent_instance.memory.get_conversation_history(session_id)
        return JSONResponse(content={
            "success": True,
            "session_id": session_id,
            "history": history
        })
    except Exception as e:
        logger.error(f"Feil ved henting av samtalehistorikk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/stats")
async def get_memory_stats():
    """Hent hukommelse statistikk."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent ikke tilgjengelig")
    
    try:
        stats = agent_instance.get_memory_stats()
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Feil ved henting av statistikk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/examples")
async def get_examples():
    """Hent eksempel forespørsler."""
    examples = [
        {
            "title": "Værprognose",
            "query": "Hva er værutsiktene i Bergen de neste 3 dagene?",
            "description": "Få værprognose for en destinasjon"
        },
        {
            "title": "Reiserute",
            "query": "Hvordan kommer jeg meg fra Oslo til Trondheim med bil?",
            "description": "Finn reiserute mellom to steder"
        },
        {
            "title": "Komplett reiseplan",
            "query": "Planlegg en reise fra Oslo til Bergen 15. desember 2024",
            "description": "Lag komplett reiseplan med vær og rute"
        },
        {
            "title": "Vær og transport",
            "query": "Jeg skal til Stockholm i morgen, hva er værforholdene og beste reisemåte fra Oslo?",
            "description": "Kombiner vær- og reiseinformasjon"
        }
    ]
    
    return JSONResponse(content={
        "success": True,
        "examples": examples
    })

if __name__ == "__main__":
    # Kjør web server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
