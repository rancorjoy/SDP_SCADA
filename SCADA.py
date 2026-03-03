# Import Needed Libraries
import os           # Operating System Management
import time         # Time Keeping and Sleep
import pathlib      # Object-Oriented File Path Management
import json         # JSON File Management
import shutil       # Shell Utilities (High Level File Operations)
import threading    # Multithreading for Commands Outside of Loop
import flask        # Lightweight web server
import requests     # For Command Line Interface Window

# Import the scripts folder
from scripts import dataManager
from scripts import flaskConfig

# Flask Command Structure
app = flask.Flask(__name__)             # Runs Flask Thread for Command Inputs

@app.route("/initialize", methods=["POST"])
def handle_initialize():
    result = dataManager.initDataPath()
    return {"success": result}

@app.route("/migrate", methods=["POST"])
def handle_migrate():
    path = flask.request.json["path"]
    result = dataManager.migrate(path)
    return {"success": result}

@app.route("/recover", methods=["POST"])
def handle_recover():
    path = flask.request.json["path"]
    result = dataManager.recover(path)
    return {"success": result}



def main():                             # Main Method - Program Entry Point
    path = dataManager.initDataPath()   # Initialize Data Path

                                                # Start HTTP server in background thread
    app = flaskConfig.initFlask()               # Initialize Flask Application
    thread = threading.Thread(target=app.run)   # Make a new thread
    thread.daemon = True                        # Dies when main program dies
    thread.start()                              # Start the new thread

    while True:                         # Main Loop
        print("Main Loop")              # Print "Main Loop" - Temporary Logic
        time.sleep(3)                   # Wait 3 Seconds - Temporary Logic

main()  # Run Main Loop
