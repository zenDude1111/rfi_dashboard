Dash Web Application README

Quick Start
===========

Build and Run with Docker
-------------------------

1. Build Docker Image:
   - Command: `docker build -t mydashapp .`
   - This builds a Docker image named `mydashapp` based on the Dockerfile.

2. Run Container:
   - Command: `docker run -p 2718:2718 mydashapp`
   - This runs the Dash application in a Docker container, making it accessible on port 2718.

Access the application at http://localhost:2718.

Server Setup
------------

- The application uses Gunicorn as the WSGI HTTP Server to serve the Dash application.
- Gunicorn is configured in the Dockerfile CMD instruction to start with 4 worker processes and bind to `0.0.0.0:2718`.
- The Dash app is initialized in `app.py` with its Flask server instance exposed for Gunicorn to serve.

Development
-----------

- Required Python version: 3.8 or newer.
- Dependencies are managed with a `requirements.txt` file.
- Docker is used for containerization, ensuring consistent environments across development and production.

Files and Directories
---------------------

- `app.py`: Contains the Dash app initialization, layout definitions, and callback functions.
- `Dockerfile`: Defines the Docker image setup instructions, including the environment, dependencies, and the command to run the app with Gunicorn.
- `requirements.txt`: Lists all the necessary Python packages.
- `/assets`: Directory for static files like CSS and JavaScript that customize the app's appearance.
- `/pages`: Includes Python scripts for each page in the app, allowing for a modular multi-page app setup.

Structure
---------

- The Dash application is structured to support a multi-page layout, with each page's content managed in separate modules within the `/pages` directory.
- The `app.py` file serves as the entry point, configuring global aspects of the app like the navbar and the page routing mechanism.
- Static resources in the `/assets` directory automatically enhance the frontend without needing manual inclusion in the HTML layout.

