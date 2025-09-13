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
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta

from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from conversation_memory import ConversationMemory

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TravelWeatherAgent:
    """Agent som bruker MCP Travel Weather Server for reiseplanlegging."""
    
    def __init__(self, openai_api_key: str = None, mcp_server_path: str = None, 
                 memory_db_path: str = "data/conversations.db"):
        """
        Initialiser agenten.
        
        Args:
            openai_api_key: API nøkkel for OpenAI
            mcp_server_path: Sti til MCP serveren
            memory_db_path: Sti til hukommelse database
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.mcp_server_path = mcp_server_path or "mcp_server.py"
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY må være satt som miljøvariabel eller parameter")
        
        self.openai = OpenAI(api_key=self.openai_api_key)
        self.session = None
        self.tools = []
        
        # Initialiser hukommelse
        self.memory = ConversationMemory(memory_db_path)
        self.current_session_id = None
        self.user_id = "default"  # Kan utvides til å støtte flere brukere
        
    def start_new_session(self, title: str = None) -> str:
        """Start en ny samtalesesjon."""
        self.current_session_id = self.memory.create_session(self.user_id, title)
        logger.info(f"Ny sesjon startet: {self.current_session_id}")
        return self.current_session_id
    
    def load_session(self, session_id: str):
        """Last inn en eksisterende sesjon."""
        self.current_session_id = session_id
        logger.info(f"Lastet sesjon: {session_id}")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """Hent liste over tilgjengelige sesjoner."""
        return self.memory.get_sessions(self.user_id)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Hent statistikk om hukommelse."""
        return self.memory.get_database_stats()
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
        Prosesser en brukerforespørsel med hukommelse.
        
        Args:
            user_query: Brukerens spørsmål eller forespørsel
            
        Returns:
            Svar fra agenten
        """
        if not self.session:
            raise RuntimeError("Ikke tilkoblet MCP server")
        
        # Sørg for at vi har en aktiv sesjon
        if not self.current_session_id:
            self.start_new_session(f"Samtale {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        try:
            # Lagre brukerens melding
            self.memory.add_message(
                session_id=self.current_session_id,
                role="user",
                content=user_query,
                user_id=self.user_id
            )
            
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

Du husker tidligere samtaler i denne sesjonen og kan referere til dem.
Svar alltid på norsk og gi praktiske råd basert på informasjonen du får."""

            # Hent samtalehistorikk for kontekst
            conversation_history = self.memory.get_recent_context(
                session_id=self.current_session_id,
                context_window=10,  # Siste 10 meldinger
                user_id=self.user_id
            )
            
            # Bygg meldinger med historie
            messages = [
                {
                    "role": "system",
                    "content": system_message
                }
            ]
            
            # Legg til samtalehistorikk (ekskludert den nye brukerforespørselen)
            messages.extend(conversation_history[:-1] if conversation_history else [])
            
            # Legg til ny brukerforespørsel
            messages.append({
                "role": "user",
                "content": user_query
            })
            
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
                # Lagre assistent melding med verktøykall
                tool_calls_data = []
                for tool_call in assistant_message.tool_calls:
                    tool_calls_data.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                
                self.memory.add_message(
                    session_id=self.current_session_id,
                    role="assistant",
                    content=assistant_message.content or "",
                    tool_calls=tool_calls_data,
                    user_id=self.user_id
                )
                
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in assistant_message.tool_calls
                    ]
                })
                
                for tool_call in assistant_message.tool_calls:
                    # Kall MCP verktøy
                    tool_result = await self.call_tool(
                        tool_call.function.name,
                        json.loads(tool_call.function.arguments)
                    )
                    
                    # Lagre verktøyresultat
                    self.memory.add_message(
                        session_id=self.current_session_id,
                        role="tool",
                        content=tool_result,
                        metadata={"tool_call_id": tool_call.id, "tool_name": tool_call.function.name},
                        user_id=self.user_id
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
            
            # Lagre endelig assistent svar
            self.memory.add_message(
                session_id=self.current_session_id,
                role="assistant",
                content=assistant_response,
                user_id=self.user_id
            )
            
            return assistant_response
            
        except Exception as e:
            logger.error(f"Feil ved prosessering av forespørsel: {e}")
            return f"Beklager, det oppstod en feil: {str(e)}"
    
    async def interactive_mode(self):
        """Kjør agenten i interaktiv modus med hukommelse."""
        print("🌍 Travel Weather Agent - Reiseplanleggingsassistent")
        print("=" * 60)
        print("Spør meg om:")
        print("• Værprognose for en destinasjon")
        print("• Reiseruter mellom to steder")
        print("• Komplette reiseplaner med vær og ruter")
        print("\nKommandoer:")
        print("• 'ny sesjon' - Start ny samtale")
        print("• 'sesjoner' - Vis tidligere samtaler")
        print("• 'stats' - Vis hukommelse statistikk")
        print("• 'quit' - Avslutt")
        print("=" * 60)
        
        # Start ny sesjon automatisk
        self.start_new_session(f"Interaktiv sesjon {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"✅ Startet ny sesjon: {self.current_session_id}")
        
        while True:
            try:
                user_input = input("\n🗨️  Spørsmål: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'avslutt']:
                    print("👋 Ha en fin reise!")
                    break
                
                if not user_input:
                    continue
                
                # Håndter spesielle kommandoer
                if user_input.lower() in ['ny sesjon', 'new session']:
                    title = input("📝 Tittel på ny sesjon (valgfri): ").strip()
                    self.start_new_session(title if title else None)
                    print(f"✅ Ny sesjon startet: {self.current_session_id}")
                    continue
                
                if user_input.lower() in ['sesjoner', 'sessions']:
                    sessions = self.list_sessions()
                    print(f"\n📋 Dine sesjoner ({len(sessions)} totalt):")
                    for session in sessions[:10]:  # Vis de 10 siste
                        print(f"  • {session['session_id']}: {session['title']} "
                              f"({session['message_count']} meldinger, "
                              f"sist aktiv: {session['last_activity']})")
                    continue
                
                if user_input.lower() in ['stats', 'statistikk']:
                    stats = self.get_memory_stats()
                    print(f"\n📊 Hukommelse statistikk:")
                    print(f"  • Totalt meldinger: {stats['total_messages']}")
                    print(f"  • Totalt sesjoner: {stats['total_sessions']}")
                    print(f"  • Unike brukere: {stats['unique_users']}")
                    print(f"  • Database størrelse: {stats['database_size_mb']} MB")
                    continue
                
                print("\n🤔 Tenker...")
                response = await self.process_query(user_input)
                print(f"\n🤖 {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Ha en fin reise!")
                break
            except Exception as e:
                print(f"\n❌ Feil: {e}")
                logger.error(f"Feil i interaktiv modus: {e}")

async def main():
    """Hovedfunksjon."""
    # Sjekk at nødvendige miljøvariabler er satt
    required_env_vars = ["OPENAI_API_KEY", "OPENWEATHER_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Følgende miljøvariabler må være satt: {', '.join(missing_vars)}")
        print("\nEksempel på oppsett:")
        print("export OPENAI_API_KEY='your-key-here'")
        print("export OPENWEATHER_API_KEY='your-key-here'")
        print("export OPENROUTE_API_KEY='your-key-here'  # Valgfri")
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
