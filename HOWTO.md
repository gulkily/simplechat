How to build simplechat with Windsurf

We are building a Git-backed web-based messaging application with a simple backend using Python, SQLite, and GitHub APIs, along with a basic HTML/CSS/JavaScript frontend. Please help us. Use incremental development and provide all necessary code snippets step by step. Avoid using frameworks. Thank you for your help. We will provide incremental steps one by one. Please start with the README file.

Next step, please create a Python script that sets up a simple HTTP server using http.server to handle GET and POST requests. Include comments explaining each part of the code.

Next step, please create an SQLite database schema with a table named messages, storing message content, a timestamp, and a unique ID. Write the Python code to initialize this database.

Next step, please show me how to test that the server is running and responds to browser requests.

Please take into account that on this system "python" is python2, and "python3" is python3

Next step, please write Python code to push a file containing a message to a GitHub repository using Git commands or the GitHub API. Assume the repository is already cloned locally. (Show me how to create the cloned repository.)

Next step, please write a test for the git interface.

I have not provided my github token yet, should the tests be passing?

Here is the token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
This project now lives at https://www.github.com/gulkily/simplechat
Please push the current state there.

Please test the messages push/pull code again.

Please use the same repository as the project for storing messages.

Please add a POST endpoint to the HTTP server that accepts a message in JSON format, saves it to the SQLite database, and pushes it to a GitHub repository.

Please add tests for this POST endpoint that verify that a message has been stored.

Please create a GET endpoint for the HTTP server that retrieves all messages from the SQLite database and returns them as a JSON array.

Please create a GET endpoint for the HTTP server that retrieves all messages from the SQLite database and returns them as a JSON array.

Please write some tests for the GET endpoint.

Please write Python code to fetch commit messages from a GitHub repository using the GitHub REST API. Return the messages in a structured format.

Please create an HTML page with a text input field, a submit button, and an area to display messages. Write minimal CSS to make it look clean.

How do I test the application, please?

How and where do I store my github api key so that the project remembers it?

Please continue writing tests.

Please run the application so that I can test it from the browser.

Thank you! This is amazing! You can stop the server now.

Please write JavaScript code to send a message from the input field to the POST endpoint via fetch, and to periodically fetch messages from the GET endpoint to display them.

Please modify the backend to allow aggregating messages from multiple GitHub repositories. Write Python code to query and merge messages from multiple repositories.

Because the .env file is not in the repo, a new installation will not be obvious how to set it. Can you please provide for this?

Can you please add a "push" command to simplechat, which will just push the repo to github?

Please modify the setup command to allow viewing and updating individual environment variables without overwriting the entire file.


