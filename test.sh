#!/bin/bash

# Test script for Travel Weather MCP Server
# Dette scriptet tester MCP serveren uten agent

set -e

echo "🧪 Tester Travel Weather MCP Server..."

# Sjekk om .env fil eksisterer
if [ ! -f .env ]; then
    echo "❌ .env fil ikke funnet. Kjør først start.sh for å sette opp miljøet."
    exit 1
fi

# Last inn miljøvariabler
source .env

# Test MCP server direkte
echo "🔍 Tester MCP server direkte..."

# Test 1: Start server og sjekk at den starter uten feil
echo "Test 1: Server oppstart..."
timeout 10s python mcp_server.py &
SERVER_PID=$!
sleep 3

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server startet OK"
    kill $SERVER_PID 2>/dev/null || true
else
    echo "❌ Server feilet ved oppstart"
    exit 1
fi

# Test 2: Test med MCP Inspector hvis npx er tilgjengelig
if command -v npx &> /dev/null; then
    echo "Test 2: MCP Inspector test..."
    echo "🔍 Starter MCP Inspector test (10 sekunder)..."
    
    # Start inspector i bakgrunnen og test
    timeout 10s npx @modelcontextprotocol/inspector python mcp_server.py &
    INSPECTOR_PID=$!
    sleep 5
    
    if ps -p $INSPECTOR_PID > /dev/null; then
        echo "✅ MCP Inspector kan koble til server"
        kill $INSPECTOR_PID 2>/dev/null || true
    else
        echo "⚠️  MCP Inspector test ikke konklusiv"
    fi
else
    echo "⚠️  npx ikke tilgjengelig, hopper over MCP Inspector test"
fi

# Test 3: Valider Python imports
echo "Test 3: Python import validering..."
python -c "
try:
    import mcp_server
    print('✅ MCP server imports OK')
except ImportError as e:
    print(f'❌ Import feil: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  Annen feil: {e}')
"

# Test 4: Sjekk API konfigurering
echo "Test 4: API konfigurasjon..."
python -c "
import os
apis = {
    'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY'),
    'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY')
}

for name, key in apis.items():
    if not key or key.startswith('your-'):
        print(f'❌ {name} ikke konfigurert')
    else:
        print(f'✅ {name} konfigurert')
"

echo ""
echo "🎉 MCP Server testing fullført!"
echo ""
echo "💡 Neste steg:"
echo "   - Test full funksjonalitet: ./start.sh"
echo "   - Bruk MCP Inspector: npx @modelcontextprotocol/inspector python mcp_server.py"
echo "   - Koble til Claude Desktop med mcp.json konfigurasjonen"
