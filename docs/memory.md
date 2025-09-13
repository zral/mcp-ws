# Persistent Hukommelse i Travel Weather Agent

## Oversikt

Travel Weather Agent har nå persistent hukommelse som lagrer samtalehistorikk i en SQLite database. Dette gjør at agenten kan:

- Huske tidligere samtaler innenfor samme sesjon
- Referere til tidligere spørsmål og svar
- Opprettholde kontekst på tvers av app-restart
- Administrere flere samtalesesjoner

## Implementasjon

### Database Schema

SQLite database med to hovedtabeller:

#### `conversations` tabell
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,            -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    tool_calls TEXT,               -- JSON array av verktøykall
    metadata TEXT,                 -- Ekstra metadata som JSON
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `sessions` tabell
```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    title TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0
);
```

### ConversationMemory Klasse

Hovedklasse for hukommelse-håndtering:

```python
from conversation_memory import ConversationMemory

# Initialiser hukommelse
memory = ConversationMemory("data/conversations.db")

# Opprett ny sesjon
session_id = memory.create_session(user_id="bruker123", title="Min reise til Paris")

# Legg til melding
memory.add_message(
    session_id=session_id,
    role="user", 
    content="Hvordan er været i Paris?"
)

# Hent samtalehistorikk
history = memory.get_conversation_history(session_id, limit=10)

# Hent nylig kontekst for OpenAI
context = memory.get_recent_context(session_id, context_window=10)
```

## Bruk i Agenten

### Automatisk sesjonshåndtering

```python
# Agent starter automatisk ny sesjon hvis ingen er aktiv
agent = TravelWeatherAgent()
await agent.connect_to_mcp_server()

# Første spørsmål oppretter automatisk ny sesjon
response = await agent.process_query("Hvordan er været i Oslo?")

# Påfølgende spørsmål bruker samme sesjon med hukommelse
response = await agent.process_query("Og hvordan med Bergen?")
```

### Manuell sesjonshåndtering

```python
# Start ny sesjon eksplisitt
session_id = agent.start_new_session("Min reiseplanlegging")

# Bytt til eksisterende sesjon
agent.load_session("bruker123_20241214_143022")

# List alle sesjoner
sessions = agent.list_sessions()

# Hent statistikk
stats = agent.get_memory_stats()
```

## Interaktiv Modus Kommandoer

I interaktiv modus kan du bruke disse kommandoene:

- `ny sesjon` - Start ny samtale
- `sesjoner` - Vis tidligere samtaler  
- `stats` - Vis hukommelse statistikk
- `quit` - Avslutt

## Web Interface API

### Nye endepunkter for hukommelse:

#### POST `/sessions`
Opprett ny sesjon:
```json
{
  "title": "Min reise til London"
}
```

#### GET `/sessions` 
Hent liste over sesjoner

#### GET `/sessions/{session_id}/history`
Hent samtalehistorikk for sesjon

#### GET `/memory/stats`
Hent hukommelse statistikk

#### POST `/query`
Utvidet med session_id:
```json
{
  "query": "Hvordan er været?",
  "session_id": "optional_session_id"
}
```

## Docker Konfigurasjon

### Persistent Lagring

I `docker-compose.yml` er det konfigurert persistent volum:

```yaml
volumes:
  - agent-data:/app/data  # Database lagres her

volumes:
  agent-data:
    driver: local
```

### Database Plassering

- **Lokal utvikling**: `./data/conversations.db`
- **Docker container**: `/app/data/conversations.db` (mappet til volum)

## Kontekst-håndtering

### Kontekst Vindu

Agenten bruker de siste 10 meldingene som kontekst for nye spørsmål:

```python
# Hent nylig kontekst
conversation_history = self.memory.get_recent_context(
    session_id=self.current_session_id,
    context_window=10,  # Siste 10 meldinger
    user_id=self.user_id
)
```

### OpenAI Integration

Kontekst sendes til OpenAI som del av messages array:

```python
messages = [
    {"role": "system", "content": system_message},
    *conversation_history,  # Tidligere samtale
    {"role": "user", "content": user_query}  # Ny forespørsel
]
```

## Vedlikehold

### Automatisk Opprydding

```python
# Slett samtaler eldre enn 30 dager
memory.delete_old_conversations(days_old=30)

# Slett for spesifikk bruker
memory.delete_old_conversations(days_old=30, user_id="bruker123")
```

### Database Statistikk

```python
stats = memory.get_database_stats()
print(f"Totalt meldinger: {stats['total_messages']}")
print(f"Database størrelse: {stats['database_size_mb']} MB")
```

## Sikkerhet og Personvern

- Samtaler lagres lokalt i SQLite database
- Ingen data sendes til eksterne tjenester utenom OpenAI API
- Database kan enkelt slettes eller flyttes
- Støtter flere brukere med user_id feltet

## Feilhåndtering

Hukommelse systemet håndterer:
- Database opprettelse automatisk
- Manglende tabeller
- Korrupte data
- Disk plass problemer

Ved feil, fortsetter agenten å fungere uten hukommelse.

## Utvidelser

Systemet kan enkelt utvides med:
- Søk i samtalehistorikk
- Kategorisering av samtaler
- Export/import av data
- Vektor database for semantisk søk
- Brukerautentisering og roller
