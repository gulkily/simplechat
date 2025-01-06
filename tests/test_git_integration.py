#!/usr/bin/env python3

import os
import sys
import unittest
import json
from datetime import datetime, timezone

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from git_handler import GitHandler

class TestGitIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.github_token = os.environ.get('GITHUB_TOKEN')
        if not self.github_token:
            self.skipTest("GITHUB_TOKEN environment variable not set")
        
        # Initialize GitHandler
        self.git_handler = GitHandler(self.github_token)

    def test_message_push_and_verify(self):
        """Test pushing a message and verifying it exists in the repository"""
        # Create a test message
        test_message = "Test message created at {}".format(
            datetime.now(timezone.utc).isoformat()
        )
        message_id = "test_{}".format(
            datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        )

        try:
            # Store the message
            commit_hash = self.git_handler.store_message(test_message, message_id)
            self.assertIsNotNone(commit_hash)
            print(f"Message stored with commit hash: {commit_hash}")

            # Verify the message file exists
            messages_dir = os.path.join(self.git_handler.repo_path, 'messages')
            self.assertTrue(os.path.exists(messages_dir))
            
            # Find and verify the message file
            message_files = [f for f in os.listdir(messages_dir) if message_id in f]
            self.assertTrue(len(message_files) > 0)
            
            # Get the most recent message file
            message_file = sorted(message_files)[-1]
            
            # Verify file contents
            with open(os.path.join(messages_dir, message_file), 'r') as f:
                message_data = json.load(f)
                self.assertEqual(message_data['content'], test_message)
                self.assertEqual(message_data['id'], message_id)

            print(f"Message file verified: {message_file}")
            print(f"Message content verified: {test_message}")

        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

if __name__ == '__main__':
    unittest.main()
