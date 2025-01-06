#!/usr/bin/env python3

import unittest
import os
import sys
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from github_api import GitHubAPI, CommitInfo

class TestGitHubAPI(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.api = GitHubAPI("test_token")
        
        # Sample commit data for mocking
        self.sample_commits = [
            {
                "sha": "abc123",
                "commit": {
                    "message": "First commit",
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2025-01-05T20:19:29-05:00"
                    }
                },
                "html_url": "https://github.com/owner/repo/commit/abc123"
            },
            {
                "sha": "def456",
                "commit": {
                    "message": "Second commit",
                    "author": {
                        "name": "Test User",
                        "email": "test@example.com",
                        "date": "2025-01-05T20:18:29-05:00"
                    }
                },
                "html_url": "https://github.com/owner/repo/commit/def456"
            }
        ]

    def test_init_without_token(self):
        """Test initialization without token"""
        with self.assertRaises(ValueError):
            GitHubAPI(None)

    @patch('requests.get')
    def test_get_commits(self, mock_get):
        """Test fetching commits"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response
        
        # Get commits
        commits = self.api.get_commits("owner", "repo")
        
        # Verify request
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "token test_token")
        self.assertEqual(kwargs["params"]["per_page"], 30)
        
        # Verify response parsing
        self.assertEqual(len(commits), 2)
        self.assertIsInstance(commits[0], CommitInfo)
        self.assertEqual(commits[0].sha, "abc123")
        self.assertEqual(commits[0].message, "First commit")
        self.assertEqual(commits[0].author_name, "Test User")

    @patch('requests.get')
    def test_get_commits_with_path(self, mock_get):
        """Test fetching commits for specific path"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response
        
        # Get commits with path
        commits = self.api.get_commits("owner", "repo", path="src/")
        
        # Verify path parameter
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["path"], "src/")

    @patch('requests.get')
    def test_get_commits_with_dates(self, mock_get):
        """Test fetching commits with date range"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response
        
        # Get commits with date range
        since = "2025-01-01T00:00:00Z"
        until = "2025-01-05T00:00:00Z"
        commits = self.api.get_commits("owner", "repo", since=since, until=until)
        
        # Verify date parameters
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"]["since"], since)
        self.assertEqual(kwargs["params"]["until"], until)

    @patch('requests.get')
    def test_get_commit_messages(self, mock_get):
        """Test fetching just commit messages"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response
        
        # Get messages
        messages = self.api.get_commit_messages("owner", "repo", max_commits=2)
        
        # Verify results
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "First commit")
        self.assertEqual(messages[1], "Second commit")

    @patch('requests.get')
    def test_error_handling(self, mock_get):
        """Test error handling"""
        # Test 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.side_effect = requests.exceptions.RequestException(response=mock_response)
        
        with self.assertRaises(ValueError) as cm:
            self.api.get_commits("owner", "nonexistent")
        self.assertIn("not found", str(cm.exception))
        
        # Test 403
        mock_response.status_code = 403
        mock_get.side_effect = requests.exceptions.RequestException(response=mock_response)
        
        with self.assertRaises(ValueError) as cm:
            self.api.get_commits("owner", "repo")
        self.assertIn("rate limit exceeded", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
