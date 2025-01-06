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
        # Initialize parent class first
        super().__init__(*args, **kwargs)
        
        # Initialize database manager
        self.db_manager = DatabaseManager()
        
        # Initialize git handler
        github_token = os.environ.get('GITHUB_TOKEN')
        if github_token:
            self.git_handler = GitHandler(github_token)
        else:
            self.git_handler = None
            print("Warning: GITHUB_TOKEN not set. Git functionality will be disabled.")

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/":
            # Serve the main page
            self.serve_file("templates/index.html", "text/html")
        elif parsed_path.path.startswith("/static/"):
            # Serve static files (CSS, JS)
            relative_path = parsed_path.path[8:]  # Remove '/static/' prefix
            self.serve_static_file(relative_path)
        elif parsed_path.path == "/messages":
            # Return messages from database
            try:
                # Parse query parameters
                query = parse_qs(parsed_path.query)
                
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
        else:
            # Handle 404
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/messages":
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

    def serve_file(self, relative_path, content_type):
        """Serve a file with the specified content type"""
        try:
            file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)
            with open(file_path, 'rb') as f:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")

    def serve_static_file(self, relative_path):
        """Serve static files with appropriate content types"""
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        
        file_ext = os.path.splitext(relative_path)[1]
        content_type = content_types.get(file_ext, 'application/octet-stream')
        
        try:
            file_path = os.path.join(STATIC_DIR, relative_path)
            with open(file_path, 'rb') as f:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(f.read())
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
