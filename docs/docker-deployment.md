# Docker Deployment Guide - Mikroservice Arkitektur

## Oversikt

**Ingrids Reisetjenester** er designet som en moderne mikroservice-arkitektur med tre separate HTTP-baserte tjenester. Denne guiden dekker alt du trenger for å sette opp systemet med Docker Compose.

## 🏗️ Mikroservice Arkitektur

Systemet består av tre isolerte mikrotjenester:

### Tjenestearkitektur
```
┌─────────────────┐    HTTP     ┌─────────────────┐    HTTP     ┌─────────────────┐
│   Web Service   │ ─────────► │  Agent Service  │ ─────────► │  MCP Server     │
│   (Port 8080)   │            │   (Port 8001)   │            │   (Port 8000)   │
│ services/web/   │            │ services/agent/ │            │services/mcp-    │
│                 │            │                 │            │    server/      │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

### 1. MCP Server (`travel-weather-mcp-server`)
**Services kataloger**: `services/mcp-server/`
- **Port**: 8000
- **Ansvar**: Pure verktøy-API for værdata og reiseplanlegging
- **API Endpoints**: `/weather`, `/routes`, `/plan`, `/health`
- **Eksterne API-er**: OpenWeatherMap, Nominatim, OpenRouteService

### 2. Agent Service (`travel-weather-agent`)  
**Services kataloger**: `services/agent/`
- **Port**: 8001
- **Ansvar**: AI-orkestrering med OpenAI GPT-4o
- **API Endpoints**: `/query`, `/health`
- **Funksjoner**: Function calling, samtalehistorikk, HTTP client til MCP

### 3. Web Service (`travel-weather-web`)
**Services kataloger**: `services/web/`
- **Port**: 8080
- **Ansvar**: Frontend web-grensesnitt 
- **API Endpoints**: `/`, `/query`, `/examples`, `/health`
- **Funksjoner**: HTML UI, HTTP client til Agent service

## Forutsetninger

- Docker Engine 20.10+ installert
- Docker Compose 2.0+ installert
- API nøkler for:
  - OpenAI (kreves)
  - OpenWeatherMap (kreves)
  - OpenRouteService (valgfri)

## 🚀 Rask Start

### 1. Forberedelse

```bash
# Klon prosjektet
git clone <repository-url>
cd agent

# Kopier miljøvariabler
cp .env.example .env

# Rediger .env med dine API nøkler
nano .env
```

### 2. Start systemet

```bash
# Automatisk setup og start
./start.sh

# ELLER manuelt:
docker-compose build
docker-compose up -d
```

### 3. Verifiser deployment

```bash
# Sjekk container status
docker-compose ps

# Sjekk helsestatuser
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Agent Service  
curl http://localhost:8080/health  # Web Service

# Tilgang til hovedside
open http://localhost:8080
```

### 3. Verifiser deployment

```bash
# Sjekk at alle containere kjører
docker-compose ps

# Test web interface
curl http://localhost:8080/health

# Test CLI agent
docker exec -it travel-weather-agent python simple_agent.py "Hvordan er været i Oslo?"
```

## Bruk av systemet

### Web Interface

Åpne http://localhost:8080 i nettleseren for grafisk grensesnitt.

### REST API

```bash
# Spørsmål via API
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Planlegg en reise fra Oslo til Bergen i morgen"}'

# Hent tilgjengelige verktøy
curl http://localhost:8080/tools

# Helse sjekk
curl http://localhost:8080/health
```

### CLI Agent

```bash
# Enkelt spørsmål
docker exec -it travel-weather-agent python simple_agent.py "Ditt spørsmål her"

# Interaktiv modus
docker exec -it travel-weather-agent python simple_agent.py

# Med shell tilgang
docker exec -it travel-weather-agent bash
```

## Persistent Data

Systemet bruker Docker volumes for å bevare data:

- `agent-data`: SQLite database med samtalehistorikk
- `logs`: Loggfiler fra alle tjenester

```bash
# Se volumes
docker volume ls | grep travel-weather

# Backup av database
docker cp travel-weather-agent:/data/conversations.db ./backup-conversations.db
```

## Feilsøking

### Sjekk containerstatus
```bash
docker-compose ps
docker-compose logs <service-name>
```

### Vanlige problemer

**Container restarter kontinuerlig:**
```bash
# Sjekk logger
docker-compose logs travel-weather-agent
```

**API nøkler ikke konfigurert:**
```bash
# Verifiser .env innstillinger
cat .env

# Restart etter endringer
docker-compose down
docker-compose up -d
```

**Port konflikter:**
```bash
# Sjekk hvilke porter som brukes
netstat -tulpn | grep :8080

# Endre port i docker-compose.yml hvis nødvendig
```

### Debug containere

```bash
# Tilgang til container shell
docker exec -it travel-weather-web bash
docker exec -it travel-weather-agent bash

# Se miljøvariabler i container
docker exec travel-weather-agent env
```

## Vedlikehold

### Oppdatere systemet
```bash
# Stopp tjenester
docker-compose down

# Oppdater kode
git pull

# Rebuild og restart
docker-compose build
docker-compose up -d
```

### Rense systemet
```bash
# Stopp og fjern containere
docker-compose down

# Fjern images (valgfri)
docker-compose down --rmi all

# Fjern volumes (mister data!)
docker-compose down --volumes
```

## Produksjon Konfigurasjon

For produksjonsmiljø, vurder følgende endringer:

### docker-compose.prod.yml
```yaml
services:
  agent-web:
    environment:
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
```

### Sikkerhet
- Bruk secrets for API nøkler i stedet for .env
- Aktiver HTTPS med reverse proxy
- Begrens container tillatelser

### Overvåkning
- Legg til Prometheus metrics
- Konfigurer log aggregering
- Sett opp health checks

## Ytelse

### Ressursbruk
- Web container: ~100-200MB RAM
- Agent container: ~50-100MB RAM  
- MCP server: ~50MB RAM

### Skalering
Systemet kan skaleres horisontalt ved å kjøre flere web interface containere bak en load balancer.

```yaml
# docker-compose.scale.yml
services:
  agent-web:
    scale: 3
  nginx:
    image: nginx
    ports:
      - "8080:80"
```
