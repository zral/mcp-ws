"""
Persistent Conversation Memory for Travel Weather Agent

Håndterer lagring og henting av samtalehistorikk med SQLite database.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Persistent hukommelse for samtaler med SQLite database."""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        """
        Initialiser hukommelse med database.
        
        Args:
            db_path: Sti til SQLite database fil
        """
        self.db_path = db_path
        
        # Opprett data katalog hvis den ikke eksisterer
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialiser database
        self._init_database()
        
    def _init_database(self):
        """Opprett database tabeller hvis de ikke eksisterer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Hovedtabell for samtaler
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabell for brukersesjon metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    title TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)
            
            # Indekser for bedre ytelse
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user_session 
                ON conversations(user_id, session_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
                ON conversations(timestamp)
            """)
            
            conn.commit()
            logger.info(f"Database initialisert: {self.db_path}")
    
    def create_session(self, user_id: str = "default", title: Optional[str] = None) -> str:
        """
        Opprett ny samtalesesjon.
        
        Args:
            user_id: Bruker ID
            title: Valgfri tittel på sesjonen
            
        Returns:
            Session ID
        """
        session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, user_id, title)
                VALUES (?, ?, ?)
            """, (session_id, user_id, title))
            conn.commit()
            
        logger.info(f"Ny sesjon opprettet: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, 
                   tool_calls: Optional[List[Dict]] = None,
                   metadata: Optional[Dict] = None,
                   user_id: str = "default"):
        """
        Legg til melding i samtalehistorikk.
        
        Args:
            session_id: Sesjon ID
            role: Rolle (user, assistant, system, tool)
            content: Meldingsinnhold
            tool_calls: Eventuelle verktøykall
            metadata: Ekstra metadata
            user_id: Bruker ID
        """
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        metadata_json = json.dumps(metadata) if metadata else None
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Legg til melding
            cursor.execute("""
                INSERT INTO conversations (user_id, session_id, role, content, tool_calls, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, session_id, role, content, tool_calls_json, metadata_json))
            
            # Oppdater sesjon statistikk
            cursor.execute("""
                UPDATE sessions 
                SET last_activity = CURRENT_TIMESTAMP,
                    message_count = message_count + 1
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
    
    def get_conversation_history(self, session_id: str, 
                               limit: int = 50,
                               user_id: str = "default") -> List[Dict[str, Any]]:
        """
        Hent samtalehistorikk for en sesjon.
        
        Args:
            session_id: Sesjon ID
            limit: Maksimalt antall meldinger
            user_id: Bruker ID
            
        Returns:
            Liste med meldinger
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, tool_calls, metadata, timestamp
                FROM conversations
                WHERE user_id = ? AND session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            """, (user_id, session_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                role, content, tool_calls_json, metadata_json, timestamp = row
                
                message = {
                    "role": role,
                    "content": content,
                    "timestamp": timestamp
                }
                
                if tool_calls_json:
                    message["tool_calls"] = json.loads(tool_calls_json)
                
                if metadata_json:
                    message["metadata"] = json.loads(metadata_json)
                
                messages.append(message)
            
            return messages
    
    def get_recent_context(self, session_id: str, 
                          context_window: int = 10,
                          user_id: str = "default") -> List[Dict[str, Any]]:
        """
        Hent nylige meldinger for kontekst.
        
        Args:
            session_id: Sesjon ID
            context_window: Antall nylige meldinger å inkludere
            user_id: Bruker ID
            
        Returns:
            Liste med nylige meldinger formatert for OpenAI
        """
        messages = self.get_conversation_history(session_id, context_window, user_id)
        
        # Konverter til OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {
                "role": msg["role"],
                "content": msg["content"]
            }
            
            # Legg til tool_calls hvis de finnes
            if "tool_calls" in msg and msg["tool_calls"]:
                openai_msg["tool_calls"] = msg["tool_calls"]
            
            openai_messages.append(openai_msg)
        
        return openai_messages
    
    def get_sessions(self, user_id: str = "default", 
                    limit: int = 20) -> List[Dict[str, Any]]:
        """
        Hent liste over sesjoner for en bruker.
        
        Args:
            user_id: Bruker ID
            limit: Maksimalt antall sesjoner
            
        Returns:
            Liste med sesjon informasjon
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, title, created_at, last_activity, message_count
                FROM sessions
                WHERE user_id = ?
                ORDER BY last_activity DESC
                LIMIT ?
            """, (user_id, limit))
            
            sessions = []
            for row in cursor.fetchall():
                session_id, title, created_at, last_activity, message_count = row
                sessions.append({
                    "session_id": session_id,
                    "title": title or "Uten tittel",
                    "created_at": created_at,
                    "last_activity": last_activity,
                    "message_count": message_count
                })
            
            return sessions
    
    def delete_old_conversations(self, days_old: int = 30, 
                               user_id: Optional[str] = None):
        """
        Slett gamle samtaler for å spare plass.
        
        Args:
            days_old: Antall dager gamle samtaler som skal slettes
            user_id: Spesifikk bruker ID, eller None for alle brukere
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    DELETE FROM conversations 
                    WHERE user_id = ? AND timestamp < ?
                """, (user_id, cutoff_date))
                
                cursor.execute("""
                    DELETE FROM sessions 
                    WHERE user_id = ? AND last_activity < ?
                """, (user_id, cutoff_date))
            else:
                cursor.execute("""
                    DELETE FROM conversations 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                cursor.execute("""
                    DELETE FROM sessions 
                    WHERE last_activity < ?
                """, (cutoff_date,))
            
            deleted_conversations = cursor.rowcount
            conn.commit()
            
            logger.info(f"Slettet {deleted_conversations} gamle samtaler eldre enn {days_old} dager")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Hent statistikk om databasen.
        
        Returns:
            Dictionary med database statistikk
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Antall samtaler
            cursor.execute("SELECT COUNT(*) FROM conversations")
            total_messages = cursor.fetchone()[0]
            
            # Antall sesjoner
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Antall unike brukere
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM sessions")
            unique_users = cursor.fetchone()[0]
            
            # Database størrelse
            db_size = Path(self.db_path).stat().st_size / (1024 * 1024)  # MB
            
            return {
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "unique_users": unique_users,
                "database_size_mb": round(db_size, 2),
                "database_path": self.db_path
            }
