"""
Simplified Travel Weather Agent for Web Interface

Denne agenten bruker MCP server funksjonaliteten direkte uten stdio kommunikasjon,
noe som fungerer bedre i Docker containere.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import openai
from openai import OpenAI

from conversation_memory import ConversationMemory
from mcp_server import get_weather_forecast, get_travel_routes, plan_trip

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTravelWeatherAgent:
    """
    Forenklet Travel Weather Agent som bruker MCP funksjonalitet direkte.
    """
    
    def __init__(self, memory_db_path: str = "/data/conversations.db"):
        """Initialiser agenten."""
        self.memory = ConversationMemory(memory_db_path)
        self.current_session_id = None
        
        # Initialiser OpenAI klient
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY miljøvariabel må være satt")
        
        self.client = OpenAI(api_key=api_key)
        
        # Definer tilgjengelige verktøy for OpenAI
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
                                "description": "Stedsnavn eller adresse for værutsikt"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Antall dager fremover (standard: 5, maks: 5)",
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
                                "description": "Utgangspunkt for reisen"
                            },
                            "destination": {
                                "type": "string",
                                "description": "Destinasjon for reisen"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Transportmiddel: driving, walking, cycling",
                                "enum": ["driving", "walking", "cycling"],
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
                                "description": "Utgangspunkt for reisen"
                            },
                            "destination": {
                                "type": "string",
                                "description": "Destinasjon for reisen"
                            },
                            "travel_date": {
                                "type": "string",
                                "description": "Reisedato i YYYY-MM-DD format"
                            },
                            "mode": {
                                "type": "string",
                                "description": "Transportmiddel: driving, walking, cycling",
                                "enum": ["driving", "walking", "cycling"],
                                "default": "driving"
                            }
                        },
                        "required": ["origin", "destination", "travel_date"]
                    }
                }
            }
        ]
        
        logger.info("SimpleTravelWeatherAgent initialisert")

    def start_new_session(self, name: str = "Default Session") -> str:
        """Start en ny samtale sesjon."""
        self.current_session_id = self.memory.create_session(name)
        logger.info(f"Ny sesjon startet: {self.current_session_id}")
        return self.current_session_id

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Kall et verktøy direkte."""
        try:
            if tool_name == "get_weather_forecast":
                return await get_weather_forecast(
                    location=arguments["location"],
                    days=arguments.get("days", 5)
                )
            elif tool_name == "get_travel_routes":
                return await get_travel_routes(
                    origin=arguments["origin"],
                    destination=arguments["destination"],
                    mode=arguments.get("mode", "driving")
                )
            elif tool_name == "plan_trip":
                return await plan_trip(
                    origin=arguments["origin"],
                    destination=arguments["destination"],
                    travel_date=arguments["travel_date"],
                    mode=arguments.get("mode", "driving")
                )
            else:
                return f"Ukjent verktøy: {tool_name}"
        except Exception as e:
            logger.error(f"Feil ved kall til {tool_name}: {e}")
            return f"Feil ved kall til {tool_name}: {str(e)}"

    async def process_query(self, query: str) -> str:
        """
        Prosesser en brukerforespørsel med OpenAI og MCP verktøy.
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
                    "content": """Du er en Travel Weather Assistant som hjelper brukere med reiseplanlegging basert på værutsikter.

Du har tilgang til disse verktøyene:
- get_weather_forecast: Hent værprognose for en destinasjon
- get_travel_routes: Hent reiseruter mellom to destinasjoner  
- plan_trip: Lag komplett reiseplan med vær og rute

Du har ikke lov å svare på noe annet enn reise og vær-relatert informasjon.

Bruk verktøyene når det trengs for å gi nyttige og nøyaktige svar. Vær vennlig og hjelpsom.
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
            
            # Lagre brukerens melding
            self.memory.add_message(self.current_session_id, "user", query)
            
            # Kall OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )
            
            message = response.choices[0].message
            
            # Håndter verktøykall hvis nødvendig
            if message.tool_calls:
                # Legg til assistant melding med verktøykall
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Utfør verktøykall
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Utfører verktøykall: {function_name} med args: {function_args}")
                    
                    tool_result = await self.call_tool(function_name, function_args)
                    
                    # Legg til verktøyresultat
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Få endelig svar fra OpenAI
                final_response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                final_answer = final_response.choices[0].message.content
            else:
                final_answer = message.content
            
            # Lagre assistentens svar
            self.memory.add_message(self.current_session_id, "assistant", final_answer)
            
            return final_answer
            
        except Exception as e:
            error_msg = f"Feil ved prosessering av forespørsel: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def get_stats(self) -> Dict[str, Any]:
        """Hent statistikk."""
        return self.memory.get_statistics()

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Hent alle sesjoner."""
        return self.memory.get_all_sessions()
