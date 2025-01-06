# SimpleChat

A lightweight, Git-backed web-based messaging application that allows users to communicate through a simple interface while persisting messages in both SQLite and Git.

## Features

- Simple web-based chat interface
- Message persistence using SQLite database
- Git-based message backup and version control
- No framework dependencies
- Real-time message updates

## Requirements

- Python 3.8+
- SQLite3
- Git
- GitHub Personal Access Token (for Git operations)

## Project Structure

```
simplechat/
├── README.md
├── requirements.txt
├── database/
│   └── chat.db
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
└── src/
    ├── app.py
    ├── database.py
    ├── git_handler.py
    └── message_handler.py
```

## Initial Setup

Before running SimpleChat, you need to set up your environment configuration:

1. Run the setup command:
```bash
./simplechat setup
```

This will create a `.env` file from the template. You can also provide your GitHub token and repository directly:
```bash
./simplechat setup --token your_github_token --repo username/repository
```

2. If you didn't provide the token and repository during setup, edit the `.env` file and add:
   - Your GitHub personal access token
   - Your GitHub repository information

To create a GitHub token:
1. Go to [GitHub Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Select the "repo" scope
4. Copy the generated token and add it to your `.env` file

### Environment Variables

The following environment variables can be configured in your `.env` file:

- `GITHUB_TOKEN` (required): Your GitHub personal access token
- `GITHUB_REPO` (required): Your GitHub repository (format: username/repo)
- `SERVER_PORT` (optional): Port for the web server (default: 8000)
- `DATABASE_PATH` (optional): Path to SQLite database (default: src/chat.db)
- `MESSAGES_DIR` (optional): Directory for message files (default: messages)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/simplechat.git
cd simplechat
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your GitHub Personal Access Token:
   - Create a token at https://github.com/settings/tokens
   - Set the environment variable:
     ```bash
     export GITHUB_TOKEN=your_token_here
     ```

5. Initialize the database:
```bash
python src/database.py
```

6. Run the application:
```bash
python src/app.py
```

7. Open your browser and navigate to `http://localhost:8000`

## Command Line Interface

SimpleChat comes with a command-line utility to manage the server and view statistics. Here are the available commands:

### Starting the Server
```bash
./simplechat start
```

### Stopping the Server
```bash
./simplechat stop
```

### Viewing Statistics
```bash
./simplechat stats
```

This will show you:
- Server status (running/stopped)
- Total number of messages
- Messages in the last 24 hours
- Timestamp of first and last messages
- Number of message files
- Total storage size used

### Managing Repositories
SimpleChat uses a `repos.txt` file to manage repositories. The first non-comment line is your main repository (used for pushing), and subsequent lines are repositories to pull from.

You can manage repositories using the CLI:
```bash
# List all configured repositories
./simplechat repos --list

# Add a repository to pull from
./simplechat repos --add username/repo

# Remove a repository
./simplechat repos --remove username/repo

# Set your main repository (for pushing)
./simplechat repos --set-main username/repo
```

You can also edit `repos.txt` directly. It supports comments (lines starting with #) and empty lines for better organization:
```bash
# Main repository
username/main-repo

# Team repositories
teammate1/chat-app
teammate2/chat-app

# Community repositories
community1/chat
community2/chat
# ...more repositories...
```

### Pulling Messages
Pull messages from configured repositories:
```bash
# Pull from all repositories (except main)
./simplechat pull

# Include messages from main repository
./simplechat pull --include-main

# Show more messages (default is 10)
./simplechat pull --limit 20
```

### Pushing Changes to GitHub
```bash
# Push existing commits
./simplechat push

# Add all changes and commit with a message
./simplechat push -a -m "Your commit message"

# Just add all changes (without committing)
./simplechat push -a

# Force push even if there are no changes
./simplechat push -f
```

### Getting Help
```bash
./simplechat --help
```

## Security Notes

- Never commit your GitHub token to the repository
- Keep your SQLite database file in `.gitignore`
- Regularly backup your database

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Submit a pull request

## License

MIT License - Feel free to use this project as you wish.
