#!/usr/bin/env python3

import unittest
import json
import http.client
import threading
import time
import os
import sys
import sqlite3
import socket
from datetime import datetime, timezone

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from app import ChatRequestHandler
from database import DatabaseManager
import socketserver

class TestServer(socketserver.TCPServer):
    allow_reuse_address = True  # This fixes the "Address already in use" error

def run_test_server(handler_class, db_path):
    """Run server for testing"""
    # Create handler class with test database
    class TestHandler(handler_class):
        def setup(self):
            """Initialize the handler"""
            super().setup()
            self.db_manager = DatabaseManager(db_path)
            self.git_handler = None  # Disable Git for tests
    
    with TestServer(("localhost", 8000), TestHandler) as httpd:
        httpd.serve_forever()

class TestChatApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment and start server"""
        # Use test database
        cls.test_db_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "test_messages.db"
        )
        
        # Remove test database if it exists
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        
        # Create test database
        cls.db_manager = DatabaseManager(cls.test_db_path)
        
        # Start server in a separate thread
        cls.server_thread = threading.Thread(
            target=run_test_server,
            args=(ChatRequestHandler, cls.test_db_path)
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)

    def setUp(self):
        """Set up test case"""
        self.conn = http.client.HTTPConnection("localhost", 8000)
        
        # Clear database before each test
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()

    def tearDown(self):
        """Clean up after test"""
        self.conn.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        # Remove test database
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

    def test_post_message(self):
        """Test posting a message"""
        # Prepare test message
        test_message = {
            "content": "Test message created at {}".format(
                datetime.now(timezone.utc).isoformat()
            )
        }
        
        # Send POST request
        headers = {"Content-Type": "application/json"}
        self.conn.request(
            "POST",
            "/messages",
            body=json.dumps(test_message),
            headers=headers
        )
        
        # Get response
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        
        # Parse response data
        response_data = json.loads(response.read().decode())
        
        # Verify response structure
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["message"], "Message saved")
        self.assertIn("id", response_data)
        self.assertIn("timestamp", response_data)
        
        # Get message from database
        message = self.db_manager.get_message_by_id(response_data["id"])
        
        # Verify message was stored in database
        self.assertIsNotNone(message)
        self.assertEqual(message["content"], test_message["content"])
        
        # If Git is enabled, verify Git commit hash
        if "git_commit_hash" in response_data and response_data["git_commit_hash"]:
            self.assertEqual(message["git_commit_hash"], response_data["git_commit_hash"])

    def test_post_invalid_message(self):
        """Test posting an invalid message"""
        # Test missing content
        invalid_message = {}
        
        headers = {"Content-Type": "application/json"}
        self.conn.request(
            "POST",
            "/messages",
            body=json.dumps(invalid_message),
            headers=headers
        )
        
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response
        
        # Verify no message was stored
        messages = self.db_manager.get_messages()
        self.assertEqual(len(messages), 0)

    def test_post_invalid_json(self):
        """Test posting invalid JSON"""
        # Send invalid JSON
        headers = {"Content-Type": "application/json"}
        self.conn.request(
            "POST",
            "/messages",
            body="invalid json",
            headers=headers
        )
        
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response
        
        # Verify no message was stored
        messages = self.db_manager.get_messages()
        self.assertEqual(len(messages), 0)

    def test_get_messages(self):
        """Test getting messages after posting"""
        # Post multiple messages
        test_messages = [
            {"content": f"Test message {i}"} for i in range(3)
        ]
        
        headers = {"Content-Type": "application/json"}
        for message in test_messages:
            self.conn.request(
                "POST",
                "/messages",
                body=json.dumps(message),
                headers=headers
            )
            response = self.conn.getresponse()
            response.read()  # Clear the response
        
        # Get messages
        self.conn.request("GET", "/messages")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        
        # Parse response data
        response_data = json.loads(response.read().decode())
        
        # Verify messages were returned
        self.assertIn("messages", response_data)
        self.assertEqual(len(response_data["messages"]), 3)
        
        # Verify message order (newest first)
        messages = response_data["messages"]
        for i in range(len(messages) - 1):
            self.assertGreater(
                messages[i]["timestamp"],
                messages[i + 1]["timestamp"]
            )

    def test_get_messages_pagination(self):
        """Test message pagination"""
        # Create 15 test messages
        test_messages = [
            {"content": f"Test message {i}"} for i in range(15)
        ]
        
        # Post all messages
        headers = {"Content-Type": "application/json"}
        for message in test_messages:
            self.conn.request(
                "POST",
                "/messages",
                body=json.dumps(message),
                headers=headers
            )
            response = self.conn.getresponse()
            response.read()  # Clear the response
        
        # Test default pagination (limit=100)
        self.conn.request("GET", "/messages")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        response_data = json.loads(response.read().decode())
        self.assertEqual(len(response_data["messages"]), 15)
        
        # Test custom limit
        self.conn.request("GET", "/messages?limit=5")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        response_data = json.loads(response.read().decode())
        self.assertEqual(len(response_data["messages"]), 5)
        
        # Test offset
        self.conn.request("GET", "/messages?limit=5&offset=5")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        response_data = json.loads(response.read().decode())
        self.assertEqual(len(response_data["messages"]), 5)
        
        # Verify message order (newest first)
        messages = response_data["messages"]
        for i in range(len(messages) - 1):
            self.assertGreater(
                messages[i]["timestamp"],
                messages[i + 1]["timestamp"]
            )

    def test_get_messages_invalid_params(self):
        """Test invalid parameters for GET /messages"""
        # Test invalid limit
        self.conn.request("GET", "/messages?limit=invalid")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response
        
        # Test invalid offset
        self.conn.request("GET", "/messages?offset=invalid")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response
        
        # Test negative limit
        self.conn.request("GET", "/messages?limit=-1")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response
        
        # Test negative offset
        self.conn.request("GET", "/messages?offset=-1")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 400)
        response.read()  # Clear the response

    def test_get_messages_empty_db(self):
        """Test getting messages from empty database"""
        # Clear database
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()
        
        # Get messages
        self.conn.request("GET", "/messages")
        response = self.conn.getresponse()
        self.assertEqual(response.status, 200)
        response_data = json.loads(response.read().decode())
        self.assertEqual(len(response_data["messages"]), 0)
        self.assertIn("messages", response_data)
        self.assertEqual(response_data["messages"], [])

if __name__ == "__main__":
    unittest.main()
