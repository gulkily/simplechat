#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime
from github import Github
import json

class GitHandler:
    def __init__(self, repo_path, github_token=None):
        """
        Initialize GitHandler with local repository path and GitHub token
        :param repo_path: Path to local git repository
        :param github_token: GitHub Personal Access Token
        """
        self.repo_path = repo_path
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        # Initialize GitHub API client
        self.github = Github(self.github_token)

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

    def ensure_repo_exists(self, repo_name, remote_url):
        """
        Ensure the local repository exists and is properly configured
        :param repo_name: Name of the repository
        :param remote_url: URL of the remote repository
        """
        if not os.path.exists(self.repo_path):
            # Clone the repository if it doesn't exist
            os.makedirs(self.repo_path, exist_ok=True)
            self._run_git_command(['git', 'clone', remote_url, '.'])
        else:
            # Verify remote and update if necessary
            try:
                current_remote = self._run_git_command(['git', 'remote', 'get-url', 'origin'])
                if current_remote != remote_url:
                    self._run_git_command(['git', 'remote', 'set-url', 'origin', remote_url])
            except subprocess.CalledProcessError:
                self._run_git_command(['git', 'remote', 'add', 'origin', remote_url])

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
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{message_id}.json"
        file_path = os.path.join(messages_dir, filename)

        # Write message to file
        message_data = {
            'id': message_id,
            'content': message_content,
            'timestamp': datetime.utcnow().isoformat()
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
        # Stage the file
        self._run_git_command(['git', 'add', file_path])

        # Create commit
        commit_message = f"Add message {message_id}"
        self._run_git_command(['git', 'commit', '-m', commit_message])

        # Push to remote
        self._run_git_command(['git', 'push', 'origin', 'main'])

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
