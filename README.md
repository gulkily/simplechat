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
