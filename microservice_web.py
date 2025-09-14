#!/usr/bin/env python3
"""
Microservice Web Interface

Web interface som kaller Agent service via HTTP.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Ingrids Reisetjenester",
    description="Web grensesnitt for intelligente reisetjenester",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")

# HTTP klient for agent kall
http_client = httpx.AsyncClient()

# Request/Response modeller
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    success: bool
    response: str
    timestamp: str
    agent_connected: bool

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    agent_connected: bool

# Agent service URL
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://travel-agent:8001")

@app.on_event("startup")
async def startup_event():
    """Initialiser ved oppstart."""
    logger.info("Starter Ingrids Reisetjenester Web Interface...")
    logger.info(f"Agent service URL: {AGENT_SERVICE_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup ved nedstengning."""
    await http_client.aclose()
    logger.info("Web interface avsluttet")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Hjem side med web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Helse sjekk."""
    # Sjekk om agent service er tilgjengelig
    agent_connected = False
    try:
        response = await http_client.get(f"{AGENT_SERVICE_URL}/health", timeout=5.0)
        agent_connected = response.status_code == 200
    except:
        pass
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        agent_connected=agent_connected
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    """Prosesser brukerforespørsel via agent service."""
    try:
        logger.info(f"Sender query til agent service: {query_request.query}")
        
        # Kall agent service
        response = await http_client.post(
            f"{AGENT_SERVICE_URL}/query",
            json={"query": query_request.query},
            timeout=30.0
        )
        response.raise_for_status()
        
        result = response.json()
        
        return QueryResponse(
            success=True,
            response=result.get("response", "Ingen svar mottatt"),
            timestamp=datetime.now().isoformat(),
            agent_connected=True
        )
        
    except httpx.TimeoutException:
        logger.error("Timeout ved kall til agent service")
        raise HTTPException(status_code=504, detail="Agent service timeout")
    except httpx.ConnectError:
        logger.error("Kan ikke koble til agent service")
        raise HTTPException(status_code=503, detail="Agent service ikke tilgjengelig")
    except Exception as e:
        logger.error(f"Feil ved prosessering: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/examples")
async def examples():
    """Eksempel forespørsler."""
    return {
        "examples": [
            {
                "title": "🌤️ Værprognose",
                "description": "Få detaljert værmelding for din destinasjon",
                "query": "Hva er været i Oslo denne uka?"
            },
            {
                "title": "🗺️ Ruteplanlegging", 
                "description": "Finn den beste ruten mellom to byer",
                "query": "Vis meg ruten fra Oslo til Bergen"
            },
            {
                "title": "✈️ Komplett reiseplan",
                "description": "Få en fullstendig reiseplan med vær og transport",
                "query": "Planlegg en tur fra Trondheim til Tromsø neste helg"
            },
            {
                "title": "📏 Avstand og tid",
                "description": "Sjekk hvor langt det er mellom to steder",
                "query": "Hvor langt er det fra Stavanger til Kristiansand?"
            },
            {
                "title": "🌍 Internasjonalt vær",
                "description": "Få værprognose for utenlandske destinasjoner",
                "query": "Hva er værprognosen for København denne uken?"
            },
            {
                "title": "⏰ Beste reisetidspunkt",
                "description": "Få råd om når du bør reise basert på værutsikter",
                "query": "Når er det best å reise til Lofoten i oktober?"
            }
        ]
    }

if __name__ == "__main__":
    logger.info("Starting Web Interface on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
