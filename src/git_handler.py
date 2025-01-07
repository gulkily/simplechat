#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime, timezone
from github import Github, Auth
import json

class GitHandler:
    def __init__(self, github_token=None):
        """
        Initialize GitHandler with GitHub token
        :param github_token: GitHub Personal Access Token
        """
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        # Initialize GitHub API client with modern authentication
        auth = Auth.Token(self.github_token)
        self.github = Github(auth=auth)
        
        # Get the project root directory (where .git is located)
        self.repo_path = self._find_git_root()

    def _find_git_root(self):
        """Find the root directory of the Git repository"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != '/':
            if os.path.exists(os.path.join(current_dir, '.git')):
                return current_dir
            current_dir = os.path.dirname(current_dir)
        raise ValueError("Not in a Git repository")

    def _run_git_command(self, command):
        """
        Run a git command and return its output
        :param command: List containing command and its arguments
        :return: Command output as string
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e.stderr}")
            raise

    def save_message_to_file(self, message_content, message_id):
        """
        Save a message to a file in the repository
        :param message_content: Content of the message
        :param message_id: Unique identifier for the message
        :return: Path to the created file
        """
        # Create messages directory if it doesn't exist
        messages_dir = os.path.join(self.repo_path, 'messages')
        os.makedirs(messages_dir, exist_ok=True)

        # Create filename with timestamp and message ID
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{message_id}.json"
        file_path = os.path.join(messages_dir, filename)

        # Write message to file
        message_data = {
            'id': message_id,
            'content': message_content,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(message_data, f, indent=2)

        return file_path

    def commit_and_push_message(self, file_path, message_id):
        """
        Commit a message file and push it to GitHub
        :param file_path: Path to the file to commit
        :param message_id: Message ID for the commit message
        :return: Commit hash
        """
        # Stage the file first
        self._run_git_command(['git', 'add', file_path])

        # Create commit
        commit_message = f"Add message {message_id}"
        self._run_git_command(['git', 'commit', '-m', commit_message])

        # Pull latest changes with rebase
        try:
            self._run_git_command(['git', 'pull', '--rebase', 'origin', 'main'])
        except subprocess.CalledProcessError:
            # If rebase fails, try to abort it and do a regular pull
            try:
                self._run_git_command(['git', 'rebase', '--abort'])
                self._run_git_command(['git', 'pull', 'origin', 'main'])
            except subprocess.CalledProcessError:
                print("Warning: Could not pull latest changes")

        # Push to remote with token authentication
        push_url = f"https://x-access-token:{self.github_token}@github.com/gulkily/simplechat.git"
        try:
            self._run_git_command(['git', 'push', push_url, 'main'])
        except subprocess.CalledProcessError:
            # If push fails, try to force push
            print("Warning: Push failed, trying force push...")
            self._run_git_command(['git', 'push', '-f', push_url, 'main'])

        # Get commit hash
        commit_hash = self._run_git_command(['git', 'rev-parse', 'HEAD'])
        return commit_hash

    def store_message(self, message_content, message_id):
        """
        Store a message in the git repository
        :param message_content: Content of the message
        :param message_id: Unique identifier for the message
        :return: Commit hash
        """
        file_path = self.save_message_to_file(message_content, message_id)
        commit_hash = self.commit_and_push_message(file_path, message_id)
        return commit_hash
