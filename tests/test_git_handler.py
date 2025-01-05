#!/usr/bin/env python3

import unittest
import os
import sys
import tempfile
import shutil
import subprocess
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
from git_handler import GitHandler

class TestGitHandler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a temporary directory for the test repository
        self.test_dir = tempfile.mkdtemp()
        self.github_token = "test_token"
        
        # Create an instance of GitHandler with the test directory
        self.git_handler = GitHandler(self.test_dir, self.github_token)
        
        # Mock the Github instance
        self.github_mock = MagicMock()
        self.git_handler.github = self.github_mock

    def tearDown(self):
        """Clean up test fixtures after each test method"""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_run_git_command(self, mock_run):
        """Test running a git command"""
        # Configure the mock
        mock_run.return_value.stdout = "test output\n"
        mock_run.return_value.stderr = ""
        
        # Run the test
        output = self.git_handler._run_git_command(['git', 'status'])
        
        # Verify the command was called correctly
        mock_run.assert_called_once()
        self.assertEqual(output, "test output")

    @patch('subprocess.run')
    def test_ensure_repo_exists_new_repo(self, mock_run):
        """Test ensuring a new repository exists"""
        repo_name = "test-repo"
        remote_url = "https://github.com/test/test-repo.git"
        
        # Configure the mock for successful command execution
        mock_run.return_value = MagicMock(stdout="", stderr="")
        
        # Run the test
        self.git_handler.ensure_repo_exists(repo_name, remote_url)
        
        # Verify the correct commands were called
        expected_calls = [
            ['git', 'remote', 'get-url', 'origin'],
            ['git', 'remote', 'set-url', 'origin', remote_url]
        ]
        
        self.assertEqual(mock_run.call_count, len(expected_calls))
        for i, expected_call in enumerate(expected_calls):
            actual_call = mock_run.call_args_list[i][0][0]
            self.assertEqual(actual_call, expected_call)

    def test_save_message_to_file(self):
        """Test saving a message to a file"""
        message_content = "Test message"
        message_id = "test_123"
        
        # Save the message
        file_path = self.git_handler.save_message_to_file(message_content, message_id)
        
        # Verify the file exists
        self.assertTrue(os.path.exists(file_path))
        
        # Read and verify the file contents
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data['content'], message_content)
        self.assertEqual(saved_data['id'], message_id)
        self.assertTrue('timestamp' in saved_data)

    @patch('subprocess.run')
    def test_commit_and_push_message(self, mock_run):
        """Test committing and pushing a message"""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        message_id = "test_123"
        expected_hash = "abcdef123456"
        
        # Configure the mock
        mock_run.return_value.stdout = expected_hash + "\n"
        
        # Run the test
        commit_hash = self.git_handler.commit_and_push_message(test_file, message_id)
        
        # Verify the correct commands were called
        expected_calls = [
            ['git', 'add', test_file],
            ['git', 'commit', '-m', f"Add message {message_id}"],
            ['git', 'push', 'origin', 'main'],
            ['git', 'rev-parse', 'HEAD']
        ]
        
        for expected_call in expected_calls:
            mock_run.assert_any_call(
                expected_call,
                cwd=self.test_dir,
                capture_output=True,
                text=True,
                check=True
            )
        
        self.assertEqual(commit_hash, expected_hash)

    @patch('subprocess.run')
    def test_store_message(self, mock_run):
        """Test the complete message storing process"""
        message_content = "Test message"
        message_id = "test_123"
        expected_hash = "abcdef123456"
        
        # Configure the mock
        mock_run.return_value.stdout = expected_hash + "\n"
        
        # Run the test
        commit_hash = self.git_handler.store_message(message_content, message_id)
        
        # Verify a file was created in the messages directory
        messages_dir = os.path.join(self.test_dir, 'messages')
        self.assertTrue(os.path.exists(messages_dir))
        self.assertTrue(any(f.endswith('.json') for f in os.listdir(messages_dir)))
        
        # Verify the commit hash
        self.assertEqual(commit_hash, expected_hash)

    def test_missing_github_token(self):
        """Test that GitHandler raises an error when no token is provided"""
        # Try to create GitHandler without a token
        with self.assertRaises(ValueError) as context:
            GitHandler(self.test_dir, github_token=None)
        
        self.assertTrue("GitHub token is required" in str(context.exception))
        
        # Try with empty environment (simulate no GITHUB_TOKEN env var)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                GitHandler(self.test_dir)
            
            self.assertTrue("GitHub token is required" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
