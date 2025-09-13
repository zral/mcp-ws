"""
MCP Travel Weather Agent

En agent som bruker MCP Travel Weather Server til å planlegge reiser
basert på værforhold på destinasjonen.

Agenten kan:
- Svare på spørsmål om vær på en destinasjon
- Gi reiseråd basert på værforhold
- Planlegge komplette reiser med vær- og ruteinformasjon
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TravelWeatherAgent:
    """Agent som bruker MCP Travel Weather Server for reiseplanlegging."""
    
    def __init__(self, anthropic_api_key: str = None, mcp_server_path: str = None):
        """
        Initialiser agenten.
        
        Args:
            anthropic_api_key: API nøkkel for Anthropic Claude
            mcp_server_path: Sti til MCP serveren
        """
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.mcp_server_path = mcp_server_path or "mcp_server.py"
        
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY må være satt som miljøvariabel eller parameter")
        
        self.anthropic = Anthropic(api_key=self.anthropic_api_key)
        self.session = None
        self.tools = []
        
    async def connect_to_mcp_server(self):
        """Koble til MCP serveren."""
        try:
            logger.info(f"Kobler til MCP server: {self.mcp_server_path}")
            
            # Konfigurer server parametere
            server_params = StdioServerParameters(
                command="python",
                args=[self.mcp_server_path],
                env=os.environ.copy()
            )
            
            # Opprett forbindelse
            stdio_transport = await stdio_client(server_params)
            self.stdio, self.write = stdio_transport
            self.session = ClientSession(self.stdio, self.write)
            
            # Initialiser sesjon
            await self.session.initialize()
            
            # Hent tilgjengelige verktøy
            tools_response = await self.session.list_tools()
            self.tools = tools_response.tools if tools_response else []
            
            logger.info(f"Tilkoblet MCP server med {len(self.tools)} verktøy")
            for tool in self.tools:
                logger.info(f"  - {tool.name}: {tool.description}")
                
        except Exception as e:
            logger.error(f"Feil ved tilkobling til MCP server: {e}")
            raise
    
    async def disconnect(self):
        """Koble fra MCP serveren."""
        if self.session:
            await self.session.close()
            logger.info("Koblet fra MCP server")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Kall et verktøy på MCP serveren.
        
        Args:
            tool_name: Navn på verktøyet
            arguments: Argumenter til verktøyet
            
        Returns:
            Resultat fra verktøyet som tekst
        """
        if not self.session:
            raise RuntimeError("Ikke tilkoblet MCP server")
        
        try:
            logger.info(f"Kaller verktøy: {tool_name} med argumenter: {arguments}")
            result = await self.session.call_tool(tool_name, arguments)
            
            if result.content:
                # Kombiner alle tekstinnhold
                text_content = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_content.append(content.text)
                    else:
                        text_content.append(str(content))
                return "\n".join(text_content)
            else:
                return "Ingen resultat returnert"
                
        except Exception as e:
            logger.error(f"Feil ved kall til verktøy {tool_name}: {e}")
            return f"Feil ved kall til verktøy: {str(e)}"
    
    def create_tools_for_claude(self) -> List[Dict[str, Any]]:
        """Konverter MCP verktøy til Claude verktøy format."""
        claude_tools = []
        
        for tool in self.tools:
            claude_tool = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            claude_tools.append(claude_tool)
        
        return claude_tools
    
    async def process_query(self, user_query: str) -> str:
        """
        Prosesser en brukerforespørsel.
        
        Args:
            user_query: Brukerens spørsmål eller forespørsel
            
        Returns:
            Svar fra agenten
        """
        if not self.session:
            raise RuntimeError("Ikke tilkoblet MCP server")
        
        try:
            # Opprett systemmelding
            system_message = """Du er en reiseplanleggingsassistent som hjelper brukere med å planlegge reiser basert på værforhold.

Du har tilgang til følgende verktøy:
- get_weather_forecast: Hent værprognose for en destinasjon
- get_travel_routes: Hent ruter og reiseinformasjon mellom to steder
- plan_trip: Lag en komplett reiseplan med vær- og ruteinformasjon

Når brukere spør om:
- Vær: Bruk get_weather_forecast
- Reiseruter: Bruk get_travel_routes  
- Komplette reiseplaner: Bruk plan_trip

Svar alltid på norsk og gi praktiske råd basert på informasjonen du får."""

            # Opprett meldinger
            messages = [
                {
                    "role": "user",
                    "content": user_query
                }
            ]
            
            # Hent Claude verktøy
            claude_tools = self.create_tools_for_claude()
            
            # Send forespørsel til Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_message,
                messages=messages,
                tools=claude_tools
            )
            
            # Prosesser svar
            assistant_response = ""
            
            for content in response.content:
                if content.type == "text":
                    assistant_response += content.text
                elif content.type == "tool_use":
                    # Kall MCP verktøy
                    tool_result = await self.call_tool(
                        content.name,
                        content.input
                    )
                    
                    # Send verktøyresultat tilbake til Claude for endelig svar
                    followup_messages = messages + [
                        {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": content.id,
                                    "name": content.name,
                                    "input": content.input
                                }
                            ]
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": tool_result
                                }
                            ]
                        }
                    ]
                    
                    # Få endelig svar fra Claude
                    final_response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        system=system_message,
                        messages=followup_messages,
                        tools=claude_tools
                    )
                    
                    for final_content in final_response.content:
                        if final_content.type == "text":
                            assistant_response += final_content.text
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"Feil ved prosessering av forespørsel: {e}")
            return f"Beklager, det oppstod en feil: {str(e)}"
    
    async def interactive_mode(self):
        """Kjør agenten i interaktiv modus."""
        print("🌍 Travel Weather Agent - Reiseplanleggingsassistent")
        print("=" * 60)
        print("Spør meg om:")
        print("• Værprognose for en destinasjon")
        print("• Reiseruter mellom to steder")
        print("• Komplette reiseplaner med vær og ruter")
        print("\nSkriv 'quit' for å avslutte")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🗨️  Spørsmål: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'avslutt']:
                    print("👋 Ha en fin reise!")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤔 Tenker...")
                response = await self.process_query(user_input)
                print(f"\n🤖 {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Ha en fin reise!")
                break
            except Exception as e:
                print(f"\n❌ Feil: {e}")

async def main():
    """Hovedfunksjon."""
    # Sjekk at nødvendige miljøvariabler er satt
    required_env_vars = ["ANTHROPIC_API_KEY", "OPENWEATHER_API_KEY", "GOOGLE_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Følgende miljøvariabler må være satt: {', '.join(missing_vars)}")
        print("\nEksempel på oppsett:")
        print("export ANTHROPIC_API_KEY='your-key-here'")
        print("export OPENWEATHER_API_KEY='your-key-here'")
        print("export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Opprett og kjør agent
    agent = TravelWeatherAgent()
    
    try:
        await agent.connect_to_mcp_server()
        await agent.interactive_mode()
    finally:
        await agent.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
