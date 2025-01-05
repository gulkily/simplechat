#!/usr/bin/env python3

import os
import sys

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from git_handler import GitHandler

def setup_repository():
    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Please set the GITHUB_TOKEN environment variable")
        print("You can create a token at: https://github.com/settings/tokens")
        return

    # Repository configuration
    repo_name = "simplechat-messages"
    repo_path = os.path.join(os.path.dirname(__file__), "chat_repo")
    
    # Your GitHub username (replace with your actual username)
    github_username = input("Enter your GitHub username: ")
    
    # Construct the remote URL
    remote_url = f"https://github.com/{github_username}/{repo_name}.git"

    try:
        # Initialize GitHandler
        handler = GitHandler(repo_path, github_token)
        
        # Ensure repository exists locally
        handler.ensure_repo_exists(repo_name, remote_url)
        
        # Test by creating a test message
        commit_hash = handler.store_message(
            "Test message from setup script",
            "setup_test_001"
        )
        
        print(f"\nRepository setup successful!")
        print(f"Repository path: {repo_path}")
        print(f"Test commit hash: {commit_hash}")
        
    except Exception as e:
        print(f"Error setting up repository: {str(e)}")

if __name__ == "__main__":
    setup_repository()
