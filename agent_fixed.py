"""
Travel Weather Agent

En intelligent agent som kombinerer reisedata med værdata for å hjelpe 
med reiseplanlegging basert på værutsikter på destinasjonen.

Denne versjonen bruker MCP server funksjonaliteten direkte.
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Optional

from simple_agent import SimpleTravelWeatherAgent

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Hovedfunksjon som starter agenten."""
    # Sjekk for nødvendige miljøvariabler
    required_env_vars = ["OPENAI_API_KEY", "OPENWEATHER_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Følgende miljøvariabler må være satt: {', '.join(missing_vars)}")
        print("\nEksempel på oppsett:")
        print("export OPENAI_API_KEY='your-key-here'")
        print("export OPENWEATHER_API_KEY='your-key-here'")
        print("export OPENROUTE_API_KEY='your-key-here'  # Valgfri")
        sys.exit(1)

    # Sjekk om det er oppgitt en query som kommandolinjeargument
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        agent = SimpleTravelWeatherAgent()
        agent.start_new_session("CLI Session")
        
        print(f"\n🔍 Spørsmål: {query}")
        print("=" * 50)
        
        try:
            response = await agent.process_query(query)
            print(f"\n💬 Svar: {response}")
        except Exception as e:
            print(f"❌ Feil: {e}")
        
        return

    # Interaktiv modus
    agent = SimpleTravelWeatherAgent()
    agent.start_new_session("Interactive CLI Session")
    
    print("🌤️  Travel Weather Agent 🚗")
    print("=" * 40)
    print("Skriv inn spørsmål om reise og vær, eller 'quit' for å avslutte.\n")
    
    try:
        while True:
            try:
                query = input("Du: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Ha det!")
                    break
                
                if not query:
                    continue
                
                print("\n🤔 Tenker...")
                response = await agent.process_query(query)
                print(f"\n💬 Agent: {response}\n")
                print("-" * 40)
                
            except KeyboardInterrupt:
                print("\n👋 Ha det!")
                break
            except EOFError:
                print("\n👋 Ha det!")
                break
            except Exception as e:
                print(f"❌ Feil: {e}")
                
    except Exception as e:
        logger.error(f"Uventet feil: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
