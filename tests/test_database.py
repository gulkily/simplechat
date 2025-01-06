#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
from datetime import datetime, timezone
from src.database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment with a temporary database"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.db_manager = DatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_add_message(self):
        """Test adding a message to the database"""
        # Test data
        content = "Test message"
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = "test-123"

        # Add message
        self.db_manager.add_message(content, timestamp, message_id)

        # Verify message was added
        message = self.db_manager.get_message_by_id(message_id)
        self.assertIsNotNone(message)
        self.assertEqual(message['content'], content)
        self.assertEqual(message['timestamp'], timestamp)
        self.assertIsNone(message['git_commit_hash'])

    def test_get_messages_pagination(self):
        """Test message pagination"""
        # Add multiple messages
        messages = []
        for i in range(5):
            content = f"Message {i}"
            timestamp = datetime.now(timezone.utc).isoformat()
            message_id = f"test-{i}"
            self.db_manager.add_message(content, timestamp, message_id)
            messages.append((message_id, content, timestamp))

        # Test different pagination scenarios
        # Case 1: Get all messages
        result = self.db_manager.get_messages(limit=10, offset=0)
        self.assertEqual(len(result), 5)

        # Case 2: Get first 2 messages
        result = self.db_manager.get_messages(limit=2, offset=0)
        self.assertEqual(len(result), 2)

        # Case 3: Get messages with offset
        result = self.db_manager.get_messages(limit=2, offset=2)
        self.assertEqual(len(result), 2)

        # Case 4: Get messages with offset beyond total count
        result = self.db_manager.get_messages(limit=2, offset=5)
        self.assertEqual(len(result), 0)

    def test_update_git_commit_hash(self):
        """Test updating git commit hash"""
        # Add a message
        content = "Test message"
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = "test-123"
        self.db_manager.add_message(content, timestamp, message_id)

        # Update git commit hash
        commit_hash = "abc123"
        self.db_manager.update_git_commit_hash(message_id, commit_hash)

        # Verify hash was updated
        message = self.db_manager.get_message_by_id(message_id)
        self.assertEqual(message['git_commit_hash'], commit_hash)

    def test_get_message_by_id_nonexistent(self):
        """Test getting a nonexistent message"""
        message = self.db_manager.get_message_by_id("nonexistent-id")
        self.assertIsNone(message)

if __name__ == '__main__':
    unittest.main()
