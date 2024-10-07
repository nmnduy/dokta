import sqlite3
import random
import string
from datetime import datetime, timedelta
from .models import ConversationEntry, Session
import os

DB_NAME = os.environ.get("DB_NAME", f"{os.path.expanduser('~')}/.local/share/dokta.db")

def random_hash(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Functions to interact with the database
def setup_database_connection(db_name):
    conn = sqlite3.connect(db_name)
    return conn

def create_database(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS session (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT DEFAULT NULL,
        created_at TEXT NOT NULL
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS conversation_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT,
        content TEXT,
        model TEXT DEFAULT NULL,
        created_at TEXT NOT NULL,
        session_id INTEGER DEFAULT NULL
    )""")
    c.execute("""PRAGMA main.page_size = 4096;""")
    c.execute("""PRAGMA main.cache_size=10000;""")
    c.execute("""PRAGMA main.locking_mode=EXCLUSIVE;""")
    c.execute("""PRAGMA main.synchronous=NORMAL;""")
    c.execute("""PRAGMA main.journal_mode=WAL;""")
    conn.commit()
    return conn

def add_entry(conn, role, content, session_id=None, model=None):
    c = conn.cursor()
    entry = ConversationEntry(role, content, session_id, model)
    c.execute("INSERT INTO conversation_entries (role, content, model, created_at, session_id) VALUES (?, ?, ?, ?, ?)",
              (entry.role, entry.content, entry.model, entry.created_at.isoformat(), entry.session_id))
    conn.commit()
    entry.id = c.lastrowid
    return entry

def get_entries_past_week(conn, session_id=None):
    c = conn.cursor()
    one_week_ago = datetime.utcnow() - timedelta(weeks=1)
    if session_id is not None:
        c.execute("SELECT id, role, content, model, created_at, session_id FROM conversation_entries WHERE created_at >= ? AND session_id = ?", (one_week_ago.isoformat(), session_id))
    else:
        c.execute("SELECT id, role, content, model, created_at, session_id FROM conversation_entries WHERE created_at >= ?", (one_week_ago.isoformat(),))
    rows = c.fetchall()
    entries = []
    for row in rows:
        entry = ConversationEntry(row[1], row[2], row[5], row[3])
        entry.id = row[0]
        entry.created_at = datetime.fromisoformat(row[4])
        entries.append(entry)
    return entries

def delete_entry(conn, entry_id):
    c = conn.cursor()
    c.execute("DELETE FROM conversation_entries WHERE id = ?", (entry_id,))
    conn.commit()

class Db:
    def __init__(self):
        if not os.path.exists(DB_NAME):
            create_database(DB_NAME)

    def get_conn(self):
        return setup_database_connection(DB_NAME)

    def create_chat_session(self, name=None):
        if name is None:
            name = random_hash()
        session = Session(name)
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO session (name, created_at) VALUES (?, ?)", (session.name, session.created_at.isoformat()))
        conn.commit()
        session.id = c.lastrowid
        return session.id

    def find_session(self, name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM session WHERE name = ?", (name,))
        row = c.fetchone()
        if row:
            session = Session(row[1])
            session.id = row[0]
            session.created_at = datetime.fromisoformat(row[2])
            return session
        return None

    def get_all_chat_sessions(self):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM session")
        rows = c.fetchall()
        sessions = []
        for row in rows:
            session = Session(row[1])
            session.id = row[0]
            session.created_at = datetime.fromisoformat(row[2])
            sessions.append(session)
        return sessions

    def rename_chat_session(self, session_id, new_name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("UPDATE session SET name = ? WHERE id = ?", (new_name, session_id))
        conn.commit()

    def get_entries_past_week(self, session_id):
        conn = self.get_conn()
        return get_entries_past_week(conn, session_id)

    def get_last_session(self, offset=0):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM session ORDER BY created_at DESC LIMIT 1 OFFSET ?", (offset,))
        row = c.fetchone()
        if row:
            session = Session(row[1])
            session.id = row[0]
            session.created_at = datetime.fromisoformat(row[2])
            return session
        return None
