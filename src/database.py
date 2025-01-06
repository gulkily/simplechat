#!/usr/bin/env python3

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
import json

# Database configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "chat.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        """Initialize database connection"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "messages.db")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    git_commit_hash TEXT DEFAULT NULL
                )
            ''')
            conn.commit()

    def add_message(self, content, timestamp, message_id):
        """
        Add a new message to the database
        :param content: Message content
        :param timestamp: Message timestamp (ISO format)
        :param message_id: Message ID (UUID)
        :return: Message ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (id, content, timestamp) VALUES (?, ?, ?)',
                (message_id, content, timestamp)
            )
            conn.commit()
            return message_id

    def get_messages(self, limit=100, offset=0):
        """
        Get messages from the database
        :param limit: Maximum number of messages to return
        :param offset: Offset for pagination
        :return: List of messages
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, timestamp, git_commit_hash
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row['id'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'git_commit_hash': row['git_commit_hash']
                })
            return messages

    def update_git_commit_hash(self, message_id, commit_hash):
        """
        Update the Git commit hash for a message
        :param message_id: Message ID
        :param commit_hash: Git commit hash
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE messages SET git_commit_hash = ? WHERE id = ?',
                (commit_hash, message_id)
            )
            conn.commit()

    def get_message_by_id(self, message_id):
        """
        Get a message by its ID
        :param message_id: Message ID
        :return: Message data or None if not found
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, timestamp, git_commit_hash
                FROM messages
                WHERE id = ?
            ''', (message_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'git_commit_hash': row['git_commit_hash']
                }
            return None

def init_database():
    """Initialize the database with the schema"""
    db_manager = DatabaseManager()
    print("Database initialized at: {}".format(DB_PATH))

if __name__ == "__main__":
    init_database()
