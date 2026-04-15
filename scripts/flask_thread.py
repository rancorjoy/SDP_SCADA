# flask_thread
# This software thread asynchronously manages CLI and Web UI commands from one or more users

# Import Needed Libraries
import os                                       # Operating System Management
import pathlib                                  # Object-Oriented File Path Management
import json                                     # JSON File Management
import shutil                                   # Shell Utilities (High Level File Operations)
import argparse                                 # Allows Console Use of Functions with Variables
import flask                                    # Lightweight web server
import requests                                 # For Command Line Interface Window
import serial                                   # Serial Communications over USB<->USB
import serial.tools.list_ports                  # Serial communication tools for port detection

from . import data_path_utils                   # Import the data_path_utils script (current) folder
from . import dcs_dict_utils                    # Import the dcs_dict_utils script (current) folder
from . import scan_serial                       # Import the scan_serial script (current) folder

def get_path():                                 # Derives the data path when a function needs it from Pointer.json
    
    def_dataPath = "../SCADA_Data"                              # Defualt Data Path
    man_pointer = def_dataPath / pathlib.Path("Pointer.json")   # If the manual path is migrated, a pointer JSON will be left behind
                                                                # JSON should contain one field: "man_pointer" with relative data path

    man_dataPath = def_dataPath                                 # Set the default manual data path to the default data path

    try:                                                                # Try to open and load pointer file to recover manual data path
        with open(man_pointer, 'r') as pointer_file:                    # Attempt to open the pointer JSON file as pointer_file
            json_pointer = json.load(pointer_file)                      # Load the pointer JSON file into json_pointer

        if "man_pointer" in json_pointer:                                   # If the JSON file contains the required field (it should if not tampered with)...
            man_dataPath = pathlib.Path(json_pointer['man_pointer'])        # Set the manual file path to the pointed path

        else:                                                           # Pointer file exists, manual path lost: use defualt data path         
            man_dataPath = def_dataPath                                 # Ensure data path is set to default path

    except FileNotFoundError:                                           # Pointer file doesn't exist, data lives at the default path (default state)
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path

    except json.JSONDecodeError as e:                                   # Pointer file exists but contains malformed/corrupted JSON
        print(f"Warning: Pointer.json is corrupted and could not be read. FLASK falling back to default path.\n  Details: {e}")
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path

    except PermissionError as e:                                        # Pointer file exists but cannot be read (permission issue)
        print(f"Error: Could not read Pointer.json, check file permissions. FLASK falling back to default path. \n  Details: {e}")
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path

    return man_dataPath                                                 # Return detected data path


def flask_loop():                               # Method is ran in entry point - returns "app"

    app = flask.Flask(__name__)                 # Runs Flask Thread for Command Inputs

    # GENERAL COMMANDS

    @app.route("/status", methods=["GET"])                  # Status Command - displays both data paths
    def handle_status():                                    # Status Definition:
        return {                                            # Return data paths
        "man_dataPath": str(data_path_utils.man_dataPath),
        "def_dataPath": str(data_path_utils.def_dataPath)}

    # FILE PATH COMMANDS

    @app.route("/initialize", methods=["POST"])             # Initialize Command - Initializes File Structure
    def handle_initialize():                                # Initialize Definition:
        result = data_path_utils.init_data_path()           # Attempts to Initialize and Stores Result
        return {"Initialize File Path Success": result}     # Return Message

    @app.route("/migrate", methods=["POST"])    # Migrate Command - Moves File Structure to Given Location
    def handle_migrate():                       # Migrate Definition:
        path = flask.request.json["path"]       # Stores Input Field "path"
        result = data_path_utils.migrate(path)  # Attempts to Migrate and Stores Result
        return {"Migration Success": result}    # Return Message

    @app.route("/recover", methods=["POST"])    # Recover Command - Moves File Structure to Given Location WITHOUT Overwrite
    def handle_recover():                       # Recover Definition:
        path = flask.request.json["path"]       # Stores Input Field "path"
        result = data_path_utils.recover(path)  # Attempts to Recover and Stores Result
        return {"Recovery Success": result}     # Return Message
    
    # SERIAL COMMANDS

    @app.route("/listSerialPorts", methods=["POST"])        # listSerialPorts Command - Returns all connected serial devices
    def handle_listSerialPorts():                           # listSerialPorts Definition:
        result = scan_serial.list_serial_ports()            # Calls function to list all connected devices
        return {"ports": result}                            # Return Message
    
    # CONTROLLER INFO COMMANDS

    @app.route("/init_dcs_info", methods=["POST"])      # init_dcs_info Command - Initialized dcs_info folder in data path
    def handle_init_dcs_info():                         # init_dcs_info Definition:
        path = get_path()                               # Get the current data path
        result = dcs_dict_utils.init_dcs_path(path)     # Calls function to initialize dcs_info folder
        return {"Initialize DCS Info Sucsess": result}  # Return Message


    print("--- Starting Flask Server on Port 5000 ---")                     # Start the flask server
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    return app                                                              # Returns the Flask Thread Created