Flask Chat Application Documentation

Screenshot 
![350107040-7a5aeae1-a00f-404a-8e49-cdffe75050f3](https://github.com/user-attachments/assets/93111de7-4127-467c-afd0-8b52d95e6e68)

Overview

This Flask application integrates user authentication, session management, and chat interaction using OpenAI's GPT models. It uses Flask extensions such as Flask-Login for user management and Flask-SQLAlchemy for database interactions.
Dependencies

    Flask
    Flask-Login
    Flask-SQLAlchemy
    OpenAI
    uuid
    os

Configuration

Credentials and sensitive keys are set at the beginning of the application:

    openai.api_key is used to authenticate requests to OpenAI's API.
    app.secret_key is essential for securely signing the session cookie.

Models
User

    Inherits from UserMixin for Flask-Login integration.
    Represents a user with a unique id.

ChatHistory

    Stores details about each chat interaction.
    Attributes include id, session_id, user_id, role, content, timestamp, and an optional summary.

Routes
Main Routes
"/"

    Method: GET, POST
    Handles user login.
    Redirects authenticated users to their interaction history.
    Returns a login form for GET requests and handles form submission for POST.

"/logout"

    Logs out the current user and redirects to the login page.

"/interact_history"

    Displays the main chat interface.
    Requires user authentication.

"/interact_history/<session_id>"

    Provides a detailed view of the chat history for a specific session.
    Requires user authentication.

API Routes
"/api"

    Handles chat interactions.
    Accepts POST requests with a user's input, processes it using OpenAI's model, and stores the interaction.
    Returns chat history and assistant's responses.

"/api/sessions"

    Fetches summaries of all chat sessions that have a stored summary.
    Returns JSON data with session IDs and their respective summaries.

"/api/new-session"

    Creates a new chat session.
    Initializes the session in the database and returns the session ID.

Functions
load_user(user_id)

    Required by Flask-Login to load a user object from a user ID.

setup_database()

    Ensures the database is set up at startup.
    Creates necessary tables if they do not exist.

Security Considerations

    Ensure that API keys and secret keys are never hardcoded in production code.
    Use environment variables to manage sensitive data securely.
    Implement proper error handling and data validation to prevent SQL injection and XSS attacks.

Deployment

    Use environment-specific configuration classes to manage settings across development, testing, and production environments.
    Ensure the production database is securely configured and not accessible publicly.
