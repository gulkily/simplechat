#!/usr/bin/env python3

import os
import json
import tempfile
import subprocess
from typing import List, Dict, Optional
from datetime import datetime
import requests
from pathlib import Path

class MessagePuller:
    """Class to pull messages from multiple GitHub repositories"""
    
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
            "User-Agent": "SimpleChat-App"
        }
    
    def clone_repo(self, repo: str, temp_dir: str) -> Optional[str]:
        """Clone a repository to a temporary directory"""
        try:
            repo_dir = os.path.join(temp_dir, repo.replace('/', '_'))
            remote_url = f'https://x-access-token:{self.github_token}@github.com/{repo}.git'
            subprocess.run(['git', 'clone', remote_url, repo_dir], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            return repo_dir
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to clone repository {repo}")
            return None

    def get_messages_from_repo(self, repo_dir: str) -> List[Dict]:
        """Extract messages from a repository"""
        messages = []
        messages_dir = os.path.join(repo_dir, 'messages')
        
        if not os.path.exists(messages_dir):
            return messages

        # Look for both .json and .txt files
        for file_path in Path(messages_dir).glob('*.*'):
            if file_path.suffix not in ['.json', '.txt']:
                continue
                
            try:
                with open(file_path, 'r') as f:
                    if file_path.suffix == '.json':
                        # Parse JSON format
                        data = json.load(f)
                        if isinstance(data, dict):
                            # Our format
                            if 'content' in data and 'timestamp' in data:
                                messages.append({
                                    'content': data['content'],
                                    'timestamp': data['timestamp'],
                                    'source_repo': os.path.basename(repo_dir)
                                })
                            # Other possible JSON formats
                            elif 'message' in data:
                                messages.append({
                                    'content': data['message'],
                                    'timestamp': data.get('time', data.get('date', datetime.now().isoformat())),
                                    'source_repo': os.path.basename(repo_dir)
                                })
                    else:
                        # Handle text files
                        content = f.read().strip()
                        if content:
                            # Use file modification time as timestamp
                            timestamp = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                            messages.append({
                                'content': content,
                                'timestamp': timestamp,
                                'source_repo': os.path.basename(repo_dir)
                            })
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to read message file {file_path}: {e}")
                continue

        return messages

    def pull_messages(self, repos: List[str]) -> List[Dict]:
        """Pull messages from multiple repositories"""
        all_messages = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for repo in repos:
                repo = repo.strip()
                if not repo:
                    continue
                    
                print(f"Pulling messages from {repo}...")
                repo_dir = self.clone_repo(repo, temp_dir)
                if repo_dir:
                    messages = self.get_messages_from_repo(repo_dir)
                    all_messages.extend(messages)
                    print(f"Found {len(messages)} messages in {repo}")

        # Sort messages by timestamp
        all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_messages
