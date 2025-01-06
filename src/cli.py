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

def load_env():
    """Load environment variables from .env file"""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    env_file = os.path.join(root_dir, '.env')
    
    if not os.path.exists(env_file):
        print("Error: .env file not found. Run 'simplechat setup' first.")
        sys.exit(1)
        
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    # Check required variables
    required_vars = ['GITHUB_TOKEN', 'GITHUB_REPO']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Run 'simplechat setup' to configure your environment.")
        sys.exit(1)

def load_repos():
    """Load repositories from repos.txt"""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    repos_file = os.path.join(root_dir, 'repos.txt')
    
    if not os.path.exists(repos_file):
        print("Error: repos.txt not found.")
        return [], None
    
    repos = []
    main_repo = None
    
    with open(repos_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if not main_repo:
                    main_repo = line  # First non-comment line is main repo
                repos.append(line)
    
    return repos, main_repo

def save_repos(repos):
    """Save repositories to repos.txt"""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    repos_file = os.path.join(root_dir, 'repos.txt')
    
    with open(repos_file, 'r') as f:
        lines = f.readlines()
    
    # Keep comments and empty lines
    header = [line for line in lines if line.strip().startswith('#') or not line.strip()]
    
    # Write back with updated repos
    with open(repos_file, 'w') as f:
        # Write header comments
        f.writelines(header)
        
        # Write repos
        if header and not header[-1].strip():
            f.write('\n'.join(repos))
        else:
            f.write('\n' + '\n'.join(repos))
        f.write('\n')

def manage_repos(args):
    """Manage repository list"""
    repos, main_repo = load_repos()
    
    if args.list:
        if not repos:
            print("No repositories configured.")
            return
            
        print("\nConfigured Repositories:")
        print("=" * 50)
        print(f"Main: {main_repo}")
        if len(repos) > 1:
            print("\nAdditional repositories:")
            for repo in repos[1:]:
                print(f"- {repo}")
        return
    
    if args.add:
        if args.add in repos:
            print(f"Repository {args.add} is already in the list.")
            return
        repos.append(args.add)
        save_repos(repos)
        print(f"Added repository: {args.add}")
        return
    
    if args.remove:
        if args.remove == main_repo:
            print("Cannot remove main repository.")
            return
        if args.remove not in repos:
            print(f"Repository {args.remove} not found in list.")
            return
        repos.remove(args.remove)
        save_repos(repos)
        print(f"Removed repository: {args.remove}")
        return
    
    if args.set_main:
        if args.set_main not in repos:
            repos.insert(0, args.set_main)
        else:
            repos.remove(args.set_main)
            repos.insert(0, args.set_main)
        save_repos(repos)
        print(f"Set {args.set_main} as main repository")
        return
        
    print("No action specified. Use --list, --add, --remove, or --set-main")

def push_changes(args):
    """Push changes to GitHub"""
    load_env()
    
    # Get main repository
    repos, main_repo = load_repos()
    if not main_repo:
        print("Error: No main repository configured.")
        print("Use 'simplechat repos --set-main username/repo' to set your repository.")
        return
    
    github_token = os.getenv('GITHUB_TOKEN')
    
    root_dir = os.path.dirname(os.path.dirname(__file__))
    
    try:
        # Check if we're in a git repository
        os.chdir(root_dir)
        if not os.path.exists('.git'):
            print("Error: Not a git repository")
            return
        
        # Add all changes
        if args.all:
            print("Adding all changes...")
            os.system('git add .')
        
        # Check if there are changes to commit
        status = os.popen('git status --porcelain').read().strip()
        if not status and not args.force:
            print("No changes to push")
            return
        
        # Commit changes if requested
        if args.message:
            print(f"Committing changes with message: {args.message}")
            os.system(f'git commit -m "{args.message}"')
        elif status:
            print("Warning: There are uncommitted changes. Use --message to commit them.")
        
        # Push to GitHub
        print("Pushing to GitHub...")
        remote_url = f'https://x-access-token:{github_token}@github.com/{main_repo}.git'
        result = os.system(f'git push {remote_url} main')
        
        if result == 0:
            print("Successfully pushed changes to GitHub")
        else:
            print("Error: Failed to push changes")
            
    except Exception as e:
        print(f"Error pushing changes: {e}")

def pull_messages(args):
    """Pull messages from configured repositories"""
    load_env()
    
    from message_puller import MessagePuller
    
    # Get repositories from repos.txt
    repos, main_repo = load_repos()
    
    if not args.include_main:
        repos = [r for r in repos if r != main_repo]
    
    if not repos:
        print("No repositories configured for pulling messages.")
        print("Use 'simplechat repos --add username/repo' to add repositories.")
        return
    
    # Initialize puller
    puller = MessagePuller(os.getenv('GITHUB_TOKEN'))
    
    try:
        # Pull messages
        messages = puller.pull_messages(repos)
        
        if not messages:
            print("No messages found in configured repositories.")
            return
            
        # Display messages
        print(f"\nFound {len(messages)} messages from {len(repos)} repositories:")
        print("=" * 50)
        
        for msg in messages[:args.limit]:
            print(f"\nFrom: {msg['source_repo']}")
            print(f"Time: {msg['timestamp']}")
            print(f"Message: {msg['content']}")
            print("-" * 50)
            
        if len(messages) > args.limit:
            print(f"\n... and {len(messages) - args.limit} more messages")
            
    except Exception as e:
        print(f"Error pulling messages: {e}")

def setup_env(args):
    """Set up the environment configuration"""
    root_dir = os.path.dirname(os.path.dirname(__file__))
    env_template = os.path.join(root_dir, '.env.template')
    env_file = os.path.join(root_dir, '.env')

    # If no .env file exists, create it from template
    if not os.path.exists(env_file):
        if not os.path.exists(env_template):
            print("Error: .env.template file not found.")
            return
        shutil.copy2(env_template, env_file)
        print("\nCreated .env file from template.")
    
    # Load current environment variables
    from dotenv import load_dotenv, set_key
    load_dotenv(env_file)
    
    # Show current configuration if no arguments provided
    if not (args.force or args.token or args.repo):
        print("\nCurrent Configuration:")
        print("=" * 50)
        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    print(line.strip())
        print("\nTo update values, use:")
        print("  --token <token>     Update GitHub token")
        print("  --repo <repo>       Update GitHub repository")
        print("  --force            Create new .env from template")
        return

    # Handle force flag
    if args.force:
        if not os.path.exists(env_template):
            print("Error: .env.template file not found.")
            return
        shutil.copy2(env_template, env_file)
        print("\nCreated new .env file from template.")
    
    # Update individual values
    if args.token:
        set_key(env_file, "GITHUB_TOKEN", args.token)
        print("Updated GitHub token in .env file.")
    
    if args.repo:
        set_key(env_file, "GITHUB_REPO", args.repo)
        print("Updated GitHub repository in .env file.")

    # Show next steps
    if not (args.token and args.repo):
        print("\nNext steps:")
        if not os.getenv('GITHUB_TOKEN'):
            print("1. Set your GitHub token:")
            print("   ./simplechat setup --token <your_token>")
        if not os.getenv('GITHUB_REPO'):
            print("2. Set your GitHub repository:")
            print("   ./simplechat setup --repo username/repository")
        print("\nTo get a GitHub token, visit: https://github.com/settings/tokens")
        print("Required scopes: repo")

def show_help(args):
    """Show detailed help information about commands"""
    commands = {
        'start': {
            'description': 'Start the chat server',
            'usage': 'simplechat start',
            'example': 'simplechat start'
        },
        'stop': {
            'description': 'Stop the running chat server',
            'usage': 'simplechat stop',
            'example': 'simplechat stop'
        },
        'stats': {
            'description': 'Display statistics about the chat application, including message counts and storage information',
            'usage': 'simplechat stats',
            'example': 'simplechat stats'
        },
        'setup': {
            'description': 'Configure the environment with GitHub credentials and repository information',
            'usage': 'simplechat setup [--force] [--token TOKEN] [--repo USERNAME/REPO]',
            'example': 'simplechat setup --token ghp_xxxx --repo username/repo'
        },
        'push': {
            'description': 'Push local changes to the configured GitHub repository',
            'usage': 'simplechat push [-m MESSAGE] [-a] [-f]',
            'example': 'simplechat push -m "Added new messages" -a'
        },
        'pull': {
            'description': 'Pull and display messages from configured repositories',
            'usage': 'simplechat pull [--include-main] [--limit N]',
            'example': 'simplechat pull --include-main --limit 20'
        },
        'repos': {
            'description': 'Manage the list of repositories for message synchronization',
            'usage': 'simplechat repos [--list] [--add REPO] [--remove REPO] [--set-main REPO]',
            'example': 'simplechat repos --add username/repo'
        },
        'help': {
            'description': 'Show detailed help information about commands',
            'usage': 'simplechat help [COMMAND]',
            'example': 'simplechat help start'
        }
    }

    if args.command_name:
        if args.command_name in commands:
            cmd = commands[args.command_name]
            print(f"\nCommand: {args.command_name}")
            print(f"Description: {cmd['description']}")
            print(f"Usage: {cmd['usage']}")
            print(f"Example: {cmd['example']}")
        else:
            print(f"Error: Unknown command '{args.command_name}'")
            print("Use 'simplechat help' to see all available commands")
    else:
        print("\nSimpleChat - A simple chat application with GitHub integration")
        print("\nAvailable commands:")
        for cmd_name, cmd_info in commands.items():
            print(f"\n  {cmd_name}")
            print(f"    {cmd_info['description']}")

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

    # Push command
    push_parser = subparsers.add_parser('push', help='Push changes to GitHub')
    push_parser.add_argument('-m', '--message', help='Commit message')
    push_parser.add_argument('-a', '--all', action='store_true', help='Add all changes before pushing')
    push_parser.add_argument('-f', '--force', action='store_true', help='Push even if there are no changes')
    push_parser.set_defaults(func=push_changes)

    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Pull messages from configured repositories')
    pull_parser.add_argument('--include-main', action='store_true', help='Include messages from main repository')
    pull_parser.add_argument('--limit', type=int, default=10, help='Maximum number of messages to display')
    pull_parser.set_defaults(func=pull_messages)

    # Repos command
    repos_parser = subparsers.add_parser('repos', help='Manage repository list')
    repos_parser.add_argument('--list', action='store_true', help='List configured repositories')
    repos_parser.add_argument('--add', metavar='REPO', help='Add a repository (format: username/repo)')
    repos_parser.add_argument('--remove', metavar='REPO', help='Remove a repository')
    repos_parser.add_argument('--set-main', metavar='REPO', help='Set main repository for pushing')
    repos_parser.set_defaults(func=manage_repos)

    # Help command
    help_parser = subparsers.add_parser('help', help='Show detailed help information')
    help_parser.add_argument('command_name', nargs='?', help='Show help for specific command')
    help_parser.set_defaults(func=show_help)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == '__main__':
    main()
