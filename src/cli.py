#!/usr/bin/env python3

import os
import sys
import argparse
import signal
import sqlite3
import psutil
import json
import shutil
from datetime import datetime
from pathlib import Path

def find_server_pid():
    """Find the PID of the running simplechat server"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'])
                if 'src/app.py' in cmdline:
                    return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def start_server(args):
    """Start the simplechat server"""
    pid = find_server_pid()
    if pid:
        print(f"Server is already running (PID: {pid})")
        return

    server_script = os.path.join(os.path.dirname(__file__), 'app.py')
    if not os.path.exists(server_script):
        print("Error: Could not find server script")
        return

    try:
        # Start the server in the background
        os.system(f'python3 {server_script} &')
        print("Server started successfully")
    except Exception as e:
        print(f"Error starting server: {e}")

def stop_server(args):
    """Stop the simplechat server"""
    pid = find_server_pid()
    if not pid:
        print("No running server found")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        print("Server stopped successfully")
    except Exception as e:
        print(f"Error stopping server: {e}")

def get_stats(args):
    """Get statistics about the chat application"""
    db_path = os.path.join(os.path.dirname(__file__), 'chat.db')
    if not os.path.exists(db_path):
        print("Error: Database not found")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get total message count
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        # Get message count in last 24 hours
        cursor.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE timestamp > datetime('now', '-1 day')
        """)
        recent_messages = cursor.fetchone()[0]

        # Get first and last message timestamps
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages")
        first_msg, last_msg = cursor.fetchone()

        # Get storage statistics
        messages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'messages')
        if os.path.exists(messages_dir):
            message_files = len([f for f in os.listdir(messages_dir) if f.endswith('.json')])
            storage_size = sum(os.path.getsize(os.path.join(messages_dir, f)) 
                             for f in os.listdir(messages_dir) if f.endswith('.json'))
        else:
            message_files = 0
            storage_size = 0

        # Format output
        stats = {
            "Server Status": "Running" if find_server_pid() else "Stopped",
            "Total Messages": total_messages,
            "Messages (Last 24h)": recent_messages,
            "First Message": first_msg or "N/A",
            "Last Message": last_msg or "N/A",
            "Message Files": message_files,
            "Storage Size": f"{storage_size / 1024:.2f} KB"
        }

        # Print stats in a formatted way
        print("\nSimpleChat Statistics:")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key:20}: {value}")

    except Exception as e:
        print(f"Error getting statistics: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def setup_env(args):
    """Set up the environment configuration"""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    env_template = os.path.join(root_dir, '.env.template')
    env_file = os.path.join(root_dir, '.env')

    if os.path.exists(env_file):
        if not args.force:
            print("Error: .env file already exists. Use --force to overwrite.")
            return
        print("Warning: Overwriting existing .env file.")

    # If no template exists, create one
    if not os.path.exists(env_template):
        print("Error: .env.template file not found.")
        return

    # Copy template to .env if it doesn't exist or force is used
    shutil.copy2(env_template, env_file)
    print("\nCreated .env file from template.")
    
    # Get GitHub token from user if provided
    if args.token:
        with open(env_file, 'r') as f:
            content = f.read()
        content = content.replace('your_github_token_here', args.token)
        with open(env_file, 'w') as f:
            f.write(content)
        print("Updated GitHub token in .env file.")
    
    # Get repository info from user if provided
    if args.repo:
        with open(env_file, 'r') as f:
            content = f.read()
        content = content.replace('your_username/your_repo', args.repo)
        with open(env_file, 'w') as f:
            f.write(content)
        print("Updated GitHub repository in .env file.")

    print("\nNext steps:")
    if not args.token:
        print("1. Edit .env file and add your GitHub token")
    if not args.repo:
        print("2. Edit .env file and add your GitHub repository (username/repo)")
    print("\nTo get a GitHub token, visit: https://github.com/settings/tokens")
    print("Required scopes: repo")

def main():
    parser = argparse.ArgumentParser(description='SimpleChat CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start the chat server')
    start_parser.set_defaults(func=start_server)

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop the chat server')
    stop_parser.set_defaults(func=stop_server)

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show chat statistics')
    stats_parser.set_defaults(func=get_stats)

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up environment configuration')
    setup_parser.add_argument('--force', action='store_true', help='Force overwrite existing .env file')
    setup_parser.add_argument('--token', help='GitHub personal access token')
    setup_parser.add_argument('--repo', help='GitHub repository (format: username/repo)')
    setup_parser.set_defaults(func=setup_env)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == '__main__':
    main()
