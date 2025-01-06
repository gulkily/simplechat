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

    @patch.dict(os.environ, {}, clear=True)
    def test_init_without_token(self):
        """Test initialization without token"""
        with self.assertRaises(ValueError):
            GitHubAPI(None)

    @patch('requests.get')
    def test_get_commits(self, mock_get):
        """Test fetching commits"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response

        # Test getting commits
        commits = self.api.get_commits("owner", "repo")

        # Verify request was made correctly
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/commits",
            headers=self.api.headers,
            params={'per_page': 30, 'page': 1}
        )

        # Verify response parsing
        self.assertEqual(len(commits), 2)
        self.assertIsInstance(commits[0], CommitInfo)
        self.assertEqual(commits[0].sha, "abc123")
        self.assertEqual(commits[0].message, "First commit")
        self.assertEqual(commits[0].author_name, "Test User")
        self.assertEqual(commits[0].author_email, "test@example.com")
        self.assertEqual(commits[0].url, "https://github.com/owner/repo/commit/abc123")

    @patch('requests.get')
    def test_get_commits_with_filters(self, mock_get):
        """Test fetching commits with filters"""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_commits
        mock_get.return_value = mock_response

        # Test parameters
        path = "src/app.py"
        since = datetime.now() - timedelta(days=7)
        until = datetime.now()
        per_page = 50
        page = 2

        # Test getting commits with filters
        commits = self.api.get_commits(
            "owner",
            "repo",
            path=path,
            since=since.isoformat(),
            until=until.isoformat(),
            per_page=per_page,
            page=page
        )

        # Verify request was made with correct parameters
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/commits",
            headers=self.api.headers,
            params={
                'path': path,
                'since': since.isoformat(),
                'until': until.isoformat(),
                'per_page': per_page,
                'page': page
            }
        )

    @patch('requests.get')
    def test_get_commits_error(self, mock_get):
        """Test error handling when fetching commits"""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error: Not Found"
        )
        mock_get.return_value = mock_response

        # Test error handling
        with self.assertRaises(requests.exceptions.HTTPError):
            self.api.get_commits("owner", "nonexistent-repo")

if __name__ == "__main__":
    unittest.main()
