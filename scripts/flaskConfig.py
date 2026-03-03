# flask_config

# Import Needed Libraries
import flask                                    # Lightweight web server
import requests                                 # For Command Line Interface Window

from . import dataManager                       # Import the scripts (current) folder

def initFlask():                                # Method is ran in entry point - returns "app"

    app = flask.Flask(__name__)                 # Runs Flask Thread for Command Inputs

    @app.route("/initialize", methods=["POST"]) # Initialize Command - Initializes File Structure
    def handle_initialize():                    # Initialize Definition:
        result = dataManager.initDataPath()     # Attempts to Initialize and Stores Result
        return {"Initialize Success": result}   # Return Message

    @app.route("/migrate", methods=["POST"])    # Migrate Command - Moves File Structure to Given Location
    def handle_migrate():                       # Migrate Definition:
        path = flask.request.json["path"]       # Stores Input Field "path"
        result = dataManager.migrate(path)      # Attempts to Migrate and Stores Result
        return {"Migration Success": result}    # Return Message

    @app.route("/recover", methods=["POST"])    # Recover Command - Moves File Structure to Given Location WITHOUT Overwrite
    def handle_recover():                       # Recover Definition:
        path = flask.request.json["path"]       # Stores Input Field "path"
        result = dataManager.recover(path)      # Attempts to Recover and Stores Result
        return {"Recovery Success": result}     # Return Message
    
    return app                                  # Returns the Flask Thread Created