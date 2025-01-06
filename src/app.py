#!/usr/bin/env python3

import http.server
import socketserver
import json
import os
import uuid
from datetime import datetime, timezone
try:
    from urllib.parse import parse_qs, urlparse
except ImportError:
    from urlparse import parse_qs, urlparse
from http import HTTPStatus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our custom modules
from database import DatabaseManager
from git_handler import GitHandler

# Constants
HOST = "localhost"
PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

class ChatRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the chat application"""
    
    def __init__(self, *args, **kwargs):
        # Initialize database manager first
        self.db_manager = DatabaseManager()
        
        # Initialize git handler
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            self.git_handler = GitHandler(github_token)
        else:
            self.git_handler = None
            print("Warning: GITHUB_TOKEN not set. Git functionality will be disabled.")
        
        # Initialize parent class last
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_file("templates/index.html", "text/html")
        elif self.path == '/messages':
            try:
                # Parse query parameters
                query = parse_qs(urlparse(self.path).query)
                
                # Get and validate limit parameter
                try:
                    limit = int(query.get('limit', [100])[0])
                    if limit < 0:
                        raise ValueError("Limit must be non-negative")
                except ValueError:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Invalid limit parameter")
                    return
                
                # Get and validate offset parameter
                try:
                    offset = int(query.get('offset', [0])[0])
                    if offset < 0:
                        raise ValueError("Offset must be non-negative")
                except ValueError:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Invalid offset parameter")
                    return
                
                # Get messages with pagination
                messages = self.db_manager.get_messages(limit=limit, offset=offset)
                self.send_json_response({"messages": messages})
            except Exception as e:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
        elif self.path.startswith('/static/'):
            # Serve static files
            file_path = self.path[1:]  # Remove leading slash
            if file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif file_path.endswith('.css'):
                content_type = 'text/css'
            else:
                content_type = 'text/plain'
            self.serve_file(file_path, content_type)
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/messages":
            try:
                # Get the length of the request body
                content_length = int(self.headers.get('Content-Length', 0))
                # Read the request body
                post_data = self.rfile.read(content_length)
                
                # Parse the JSON data
                message_data = json.loads(post_data.decode('utf-8'))
                
                # Validate message content
                if 'content' not in message_data:
                    raise ValueError("Message content is required")
                
                # Generate message ID and timestamp
                message_id = str(uuid.uuid4())
                timestamp = datetime.now(timezone.utc).isoformat()
                
                # Save to database
                self.db_manager.add_message(
                    message_data['content'],
                    timestamp,
                    message_id
                )
                
                # Save to Git if enabled
                git_commit_hash = None
                if self.git_handler:
                    try:
                        git_commit_hash = self.git_handler.store_message(
                            message_data['content'],
                            message_id
                        )
                        # Update git commit hash in database
                        self.db_manager.update_git_commit_hash(message_id, git_commit_hash)
                    except Exception as e:
                        print(f"Warning: Failed to store message in Git: {str(e)}")
                
                # Prepare response
                response_data = {
                    "status": "success",
                    "message": "Message saved",
                    "id": message_id,
                    "timestamp": timestamp,
                    "git_commit_hash": git_commit_hash
                }
                
                self.send_json_response(response_data)
                
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON data")
            except ValueError as e:
                self.send_error(HTTPStatus.BAD_REQUEST, str(e))
            except Exception as e:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(e))
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def serve_file(self, file_path, content_type):
        """Helper method to send a file"""
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def send_json_response(self, data):
        """Helper method to send JSON responses"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

def run_server():
    """Start the HTTP server"""
    with socketserver.TCPServer((HOST, PORT), ChatRequestHandler) as httpd:
        print("Server running at http://{}:{}".format(HOST, PORT))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
