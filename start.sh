#!/bin/bash

# Travel Weather MCP System - Start Script
# Dette scriptet bygger og starter alle Docker containere

echo "��️  Travel Weather MCP System 🚗"
echo "======================================="

# Sjekk at Docker er installert
if ! command -v docker &> /dev/null; then
    echo "❌ Docker er ikke installert. Installer Docker først."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose er ikke installert. Installer Docker Compose først."
    exit 1
fi

# Sjekk at .env fil eksisterer
if [ ! -f .env ]; then
    echo "⚠️  .env fil ikke funnet. Kopierer fra .env.example..."
    cp .env.example .env
    echo "✅ .env fil opprettet. Rediger denne med dine API nøkler:"
    echo "   - OPENAI_API_KEY"
    echo "   - OPENWEATHER_API_KEY"
    echo "   - OPENROUTE_API_KEY (valgfri)"
    echo ""
    read -p "Trykk Enter når du har redigert .env filen..."
fi

echo "🔨 Bygger Docker containere..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Feil ved bygging av containere"
    exit 1
fi

echo "🚀 Starter tjenester..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Feil ved start av tjenester"
    exit 1
fi

echo "⏳ Venter på at tjenester skal starte..."
sleep 5

echo "📊 Sjekker status..."
docker-compose ps

echo ""
echo "✅ Travel Weather MCP System er startet!"
echo ""
echo "🌐 Web Interface: http://localhost:8080"
echo ""
echo "📝 CLI Bruk:"
echo "   docker exec -it travel-weather-agent python simple_agent.py \"Ditt spørsmål her\""
echo ""
echo "🔧 API Test:"
echo "   curl -X POST http://localhost:8080/query -H \"Content-Type: application/json\" -d '{\"query\": \"Hvordan er været i Oslo?\"}'"
echo ""
echo "🛑 For å stoppe systemet: docker-compose down"
