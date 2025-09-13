"""
MCP Travel Weather Agent

En agent som bruker MCP Travel Weather Server til å planlegge reiser
basert på værforhold på destinasjonen.

Agenten kan:
- Svare på spørsmål om vær på en destinasjon
- Gi reiseråd basert på værforhold
- Planlegge komplette reiser med vær- og ruteinformasjon

Bruker OpenAI GPT-4 for intelligent samtale og verktøybruk.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any
from datetime import datetime, timedelta

from openai import OpenAI
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
    
    def __init__(self, openai_api_key: str = None, mcp_server_path: str = None):
        """
        Initialiser agenten.
        
        Args:
            openai_api_key: API nøkkel for OpenAI
            mcp_server_path: Sti til MCP serveren
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.mcp_server_path = mcp_server_path or "mcp_server.py"
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY må være satt som miljøvariabel eller parameter")
        
        self.openai = OpenAI(api_key=self.openai_api_key)
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
    
    def create_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Konverter MCP verktøy til OpenAI verktøy format."""
        openai_tools = []
        
        for tool in self.tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
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
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
            
            # Hent OpenAI verktøy
            openai_tools = self.create_tools_for_openai()
            
            # Send forespørsel til OpenAI
            response = self.openai.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )
            
            # Prosesser svar
            assistant_message = response.choices[0].message
            assistant_response = ""
            
            if assistant_message.content:
                assistant_response += assistant_message.content
            
            # Håndter verktøykall
            if assistant_message.tool_calls:
                messages.append(assistant_message)
                
                for tool_call in assistant_message.tool_calls:
                    # Kall MCP verktøy
                    tool_result = await self.call_tool(
                        tool_call.function.name,
                        json.loads(tool_call.function.arguments)
                    )
                    
                    # Legg til verktøyresultat i meldinger
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Få endelig svar fra OpenAI
                final_response = self.openai.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=2000,
                    messages=messages
                )
                
                final_message = final_response.choices[0].message
                if final_message.content:
                    assistant_response = final_message.content
            
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
    required_env_vars = ["OPENAI_API_KEY", "OPENWEATHER_API_KEY", "GOOGLE_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Følgende miljøvariabler må være satt: {', '.join(missing_vars)}")
        print("\nEksempel på oppsett:")
        print("export OPENAI_API_KEY='your-key-here'")
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
