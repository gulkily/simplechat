#!/usr/bin/env python3

import unittest
from unittest.mock import patch, Mock
import os
import tempfile
import shutil
from datetime import datetime
import json
from github import Github, GithubException
from git_handler import GitHandler

class TestGitHandler(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.github_token = "test_token"
        
        # Create a mock git repo structure
        os.makedirs(os.path.join(self.test_dir, '.git'))
        
        # Patch _find_git_root to return our test directory
        patcher = patch.object(GitHandler, '_find_git_root', return_value=self.test_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.git_handler = GitHandler(self.github_token)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_github_token(self):
        """Test that GitHandler raises an error when no token is provided"""
        with self.assertRaises(ValueError):
            GitHandler(None)

    @patch('subprocess.run')
    def test_run_git_command(self, mock_run):
        """Test running a git command"""
        # Mock subprocess.run
        mock_run.return_value.stdout = "test output\n"
        mock_run.return_value.stderr = ""
        
        # Test running command
        output = self.git_handler._run_git_command(['git', 'status'])
        self.assertEqual(output, "test output")
        
        # Verify command was run with correct arguments
        mock_run.assert_called_once_with(
            ['git', 'status'],
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_store_message(self, mock_run):
        """Test storing a message"""
        # Setup test data
        message = {
            'content': 'Test message',
            'timestamp': datetime.now().isoformat()
        }
        message_id = 'test_123'
        
        # Mock git commands
        mock_run.return_value.stdout = "abc123\n"
        mock_run.return_value.stderr = ""
        
        # Mock GitHub API
        mock_repo = Mock()
        mock_github = Mock()
        mock_github.get_user.return_value.get_repo.return_value = mock_repo
        
        # Test storing message
        commit_hash = self.git_handler.store_message(message['content'], message_id)
        
        # Verify results
        self.assertEqual(commit_hash, "abc123")
        
        # Verify git commands were called in correct order
        expected_commands = [
            ['git', 'pull', '--rebase', 'origin', 'main'],
            ['git', 'add', os.path.join('messages', f'*_{message_id}.json')],
            ['git', 'commit', '-m', f'Add message {message_id}'],
            ['git', 'push', f'https://x-access-token:{self.github_token}@github.com/gulkily/simplechat.git', 'main'],
            ['git', 'rev-parse', 'HEAD']
        ]
        
        self.assertEqual(mock_run.call_count, len(expected_commands))
        for i, expected_command in enumerate(expected_commands):
            actual_command = mock_run.call_args_list[i][0][0]
            # Compare commands ignoring the exact file path for the add command
            if 'add' in actual_command:
                self.assertEqual(actual_command[0:2], expected_command[0:2])
                self.assertTrue(actual_command[2].endswith(f'_{message_id}.json'))
            else:
                self.assertEqual(actual_command, expected_command)

    @patch('subprocess.run')
    def test_save_message_to_file(self, mock_run):
        """Test saving a message to a file"""
        # Setup test data
        message = {
            'content': 'Test message',
            'timestamp': datetime.now().isoformat()
        }
        message_id = 'test_123'
        
        # Test saving message
        filename = self.git_handler.save_message_to_file(message['content'], message_id)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(filename))
        with open(filename, 'r') as f:
            saved_message = json.load(f)
            self.assertEqual(saved_message['content'], message['content'])
            self.assertEqual(saved_message['id'], message_id)
            self.assertIn('timestamp', saved_message)

if __name__ == '__main__':
    unittest.main()
