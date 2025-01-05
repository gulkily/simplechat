#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime
import json

# Database configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "chat.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        """Initialize database manager with the database path"""
        self.db_path = db_path
        self._ensure_db_directory()
        self.init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def init_db(self):
        """Initialize the database and create the messages table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    git_commit_hash TEXT
                )
            ''')
            
            # Create index on timestamp for faster querying
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON messages(timestamp)
            ''')
            
            conn.commit()

    def add_message(self, content, timestamp=None):
        """
        Add a new message to the database
        Returns the ID of the inserted message
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (content, timestamp)
                VALUES (?, ?)
            ''', (content, timestamp))
            conn.commit()
            return cursor.lastrowid

    def get_messages(self, limit=100, offset=0):
        """
        Retrieve messages from the database, ordered by timestamp
        Returns a list of dictionaries containing message data
        """
        with sqlite3.connect(self.db_path) as conn:
            # Configure connection to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, timestamp, git_commit_hash
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]

    def update_git_commit_hash(self, message_id, commit_hash):
        """Update the git commit hash for a message"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages
                SET git_commit_hash = ?
                WHERE id = ?
            ''', (commit_hash, message_id))
            conn.commit()

    def get_message_by_id(self, message_id):
        """Retrieve a specific message by its ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, timestamp, git_commit_hash
                FROM messages
                WHERE id = ?
            ''', (message_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None

def init_database():
    """Initialize the database with the schema"""
    db_manager = DatabaseManager()
    print("Database initialized at: {}".format(DB_PATH))

if __name__ == "__main__":
    init_database()
