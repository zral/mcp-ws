#!/bin/bash

# Start script for Travel Weather MCP Server og Agent
# Dette scriptet setter opp miljøet og starter tjenestene

set -e

echo "🚀 Starter Travel Weather MCP Server og Agent..."

# Sjekk om .env fil eksisterer
if [ ! -f .env ]; then
    echo "⚠️  .env fil ikke funnet. Kopierer fra .env.example..."
    cp .env.example .env
    echo "📝 Vennligst rediger .env filen med dine API nøkler før du fortsetter."
    echo "   - OPENWEATHER_API_KEY: https://openweathermap.org/api"
    echo "   - GOOGLE_API_KEY: https://console.cloud.google.com/"
    echo "   - OPENAI_API_KEY: https://platform.openai.com/"
    exit 1
fi

# Last inn miljøvariabler
source .env

# Sjekk at nødvendige API nøkler er satt
check_api_key() {
    local key_name=$1
    local key_value=${!key_name}
    
    if [ -z "$key_value" ] || [ "$key_value" = "your-${key_name,,}-here" ]; then
        echo "❌ $key_name er ikke satt eller har standardverdi"
        return 1
    fi
    echo "✅ $key_name er konfigurert"
    return 0
}

echo "🔍 Sjekker API nøkler..."
all_keys_ok=true

if ! check_api_key "OPENWEATHER_API_KEY"; then
    all_keys_ok=false
fi

if ! check_api_key "GOOGLE_API_KEY"; then
    all_keys_ok=false
fi

if ! check_api_key "OPENAI_API_KEY"; then
    all_keys_ok=false
fi

if [ "$all_keys_ok" = false ]; then
    echo "❌ En eller flere API nøkler mangler. Vennligst oppdater .env filen."
    exit 1
fi

# Sjekk om Docker er installert og kjører
if ! command -v docker &> /dev/null; then
    echo "❌ Docker er ikke installert. Vennligst installer Docker først."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker daemon kjører ikke. Vennligst start Docker."
    exit 1
fi

# Sjekk om Docker Compose er tilgjengelig
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose er ikke tilgjengelig."
    exit 1
fi

echo "🐳 Bruker: $DOCKER_COMPOSE_CMD"

# Bygg og start containere
echo "🔨 Bygger Docker images..."
$DOCKER_COMPOSE_CMD build

echo "🚀 Starter tjenester..."
$DOCKER_COMPOSE_CMD up -d

echo "⏳ Venter på at tjenester skal starte..."
sleep 10

# Sjekk status på tjenester
echo "📊 Status på tjenester:"
$DOCKER_COMPOSE_CMD ps

# Vis logfiler
echo ""
echo "📝 Logfiler for MCP Server:"
$DOCKER_COMPOSE_CMD logs --tail=10 mcp-server

echo ""
echo "📝 Logfiler for Agent:"
$DOCKER_COMPOSE_CMD logs --tail=10 travel-agent

echo ""
echo "✅ Travel Weather MCP Server og Agent er startet!"
echo ""
echo "🌐 Web Interface: http://localhost:8080"
echo "   Bruk denne for enkel interaksjon med agenten"
echo ""
echo "🔍 For debugging med MCP Inspector:"
echo "   $DOCKER_COMPOSE_CMD --profile debug up -d mcp-inspector"
echo "   Deretter gå til http://localhost:5173"
echo ""
echo "🐳 For å bruke agenten i terminal:"
echo "   $DOCKER_COMPOSE_CMD exec travel-agent python agent.py"
echo ""
echo "📊 For å se logfiler:"
echo "   $DOCKER_COMPOSE_CMD logs -f mcp-server"
echo "   $DOCKER_COMPOSE_CMD logs -f agent-web"
echo ""
echo "🛑 For å stoppe tjenestene:"
echo "   $DOCKER_COMPOSE_CMD down"
