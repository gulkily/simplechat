#!/usr/bin/env python3

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class CommitInfo:
    """Structured representation of a Git commit"""
    sha: str
    message: str
    author_name: str
    author_email: str
    timestamp: str
    url: str

class GitHubAPI:
    """Class to interact with GitHub REST API"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client
        :param token: GitHub personal access token. If not provided, will look for GITHUB_TOKEN env var
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "User-Agent": "SimpleChat-App"
        }

    def get_commits(
        self,
        owner: str,
        repo: str,
        path: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        per_page: int = 30,
        page: int = 1
    ) -> List[CommitInfo]:
        """
        Fetch commit messages from a GitHub repository
        
        :param owner: Repository owner (username or organization)
        :param repo: Repository name
        :param path: Optional path to filter commits by file/directory
        :param since: ISO 8601 timestamp to fetch commits after
        :param until: ISO 8601 timestamp to fetch commits before
        :param per_page: Number of commits per page (max 100)
        :param page: Page number for pagination
        :return: List of CommitInfo objects
        """
        # Build URL and parameters
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {
            "per_page": min(per_page, 100),  # GitHub max is 100
            "page": page
        }
        
        # Add optional parameters
        if path:
            params["path"] = path
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        try:
            # Make API request
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Parse response
            commits = []
            commit_data_list = response.json()
            if not isinstance(commit_data_list, list):
                raise ValueError("Invalid response format from GitHub API")
                
            for commit_data in commit_data_list:
                commits.append(CommitInfo(
                    sha=commit_data["sha"],
                    message=commit_data["commit"]["message"],
                    author_name=commit_data["commit"]["author"]["name"],
                    author_email=commit_data["commit"]["author"]["email"],
                    timestamp=commit_data["commit"]["author"]["date"],
                    url=commit_data["html_url"]
                ))
            
            return commits
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                raise ValueError(f"Repository {owner}/{repo} not found") from e
            elif hasattr(e.response, 'status_code') and e.response.status_code == 403:
                raise ValueError("API rate limit exceeded or insufficient permissions") from e
            else:
                raise ValueError(f"Failed to fetch commits: {str(e)}") from e

    def get_commit_messages(
        self,
        owner: str,
        repo: str,
        max_commits: int = 100,
        **kwargs
    ) -> List[str]:
        """
        Fetch just the commit messages from a repository
        
        :param owner: Repository owner
        :param repo: Repository name
        :param max_commits: Maximum number of commit messages to fetch
        :param kwargs: Additional arguments to pass to get_commits
        :return: List of commit messages
        """
        # Calculate pagination
        per_page = min(max_commits, 100)
        pages = (max_commits + per_page - 1) // per_page
        
        messages = []
        for page in range(1, pages + 1):
            commits = self.get_commits(
                owner=owner,
                repo=repo,
                per_page=per_page,
                page=page,
                **kwargs
            )
            
            # Add messages
            messages.extend(commit.message for commit in commits)
            
            # Check if we have enough messages
            if len(messages) >= max_commits:
                return messages[:max_commits]
            
            # Check if this is the last page
            if len(commits) < per_page:
                break
        
        return messages
