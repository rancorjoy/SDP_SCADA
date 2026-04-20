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
import logging                                  # For custom server logging
import sys                                      # Used at end to supress logging

from . import data_path_utils                   # Import the data_path_utils script (current) folder
from . import dcs_dict_utils                    # Import the dcs_dict_utils script (current) folder
from . import scan_serial                       # Import the scan_serial script (current) folder
from . import dcs_flash_utils                   # Import the dcs_flash_utils script
from . import print_log                

logging.getLogger('werkzeug').disabled = True           # Disable default logging (reduces clutter in main window)
logging.getLogger('werkzeug.serving').disabled = True

COMMANDS = {
    #  cmd name        min  max  usage hint
    "help":          (0,   0,   "help"),
    "status":        (0,   0,   "status"),
    "init_data":     (0,   0,   "init_data"),
    "init_info":     (0,   0,   "init_info"),
    "init_scripts":  (0,   0,   "init_scripts"),
    "migrate":       (1,   1,   "migrate <path>"),
    "recover":       (1,   1,   "recover <path>"),
    "list_serial":   (0,   0,   "list_serial"),
    "list_dcs":      (0,   0,   "list_dcs"),
    "rename_dcs":    (2,   2,   "rename_dcs <old_name> <new_name>"),
    "unload_dcs":    (1,   1,   "unload_dcs <name>"),
    "load_dcs":      (1,   1,   "load_dcs <name>"),
    "delete_dcs":    (1,   1,   "delete_dcs <name>"),
}

def get_path():                                                 # Derives the data path when a function needs it from Pointer.json
    def_dataPath = pathlib.Path("../SCADA_Data")                # Defualt Data Path
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
        print_log.pL("Server", "Error", "System Event: Warning: Pointer.json could not be read.", "System", True, {e})
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path

    except PermissionError as e:                                        # Pointer file exists but cannot be read (permission issue)
        print_log.pL("Server", "Error", "Could not read Pointer.json, check file permissions.", "System", True, {e})
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path

    return man_dataPath                                                 # Return detected data path

def validate(cmd, args):
    if cmd not in COMMANDS:
        return f"Unknown command '{cmd}'. Type 'help' for commands."
    min_args, max_args, usage = COMMANDS[cmd]
    if not (min_args <= len(args) <= max_args):
        return f"Usage: {usage}"
    if any(not str(a).strip() for a in args):
        return f"Usage: {usage}"
    return None  # None means valid

def get_help():
    help_text = f"""General Commands:
    help :             \t Displays a list of all valid commands
    status :           \t Displays the network status of the SCADA server

    Data Path Commands:
    init_data :        \t Initializes the persistent data path
    init_info :        \t Initializes the dcs information folder
    init_scripts :     \t Initializes the dcs scripts folder
    migrate <path> :   \t Migrates the persistent data path to specified location <path>
    recover <path> :   \t Recovers the persistent data path at specified location <path>

    Serial Commands:
    list_serial : \t Lists all detected serial connections to the SCADA server

    Controller Commands:
    list_dcs :     \t List all known DCS Controllers
    rename_dcs :   \t Rename a DCS Controller <old name> <new name>
    unload_dcs :   \t Remove a DCS from the current list <name>
    load_dcs :     \t Add a DCS from to current list (from file) <name>
    delete_dcs :   \t Delete a DCS Controller <name>
    """
    return help_text

def flask_loop(dcs_list):                       # Method is ran in entry point - returns "app"

    app = flask.Flask(__name__)                             # Runs Flask Thread for Command Inputs

    @app.route("/command", methods=["POST"])
    def handle_command():
        body = flask.request.json or {}
        cmd  = body.get("cmd", "").strip()
        args = [str(a).strip() for a in body.get("args", [])]

        error = validate(cmd, args)
        if error:
            return flask.jsonify({"ok": False, "message": error}), 400
        
        print_log.pL("Server", "Event", f"{cmd}, {', '.join(args)} from {flask.request.remote_addr}.", "User", False, None)

        try:
            if cmd == "help":       return {"ok": True, "message": get_help()}
            if cmd == "status":     return {"ok": True, "message": "Running"}

            if cmd == "init_data":      return {"ok": True, "result": data_path_utils.init_data_path()}
            if cmd == "init_info":      return {"ok": True, "result": dcs_dict_utils.init_dcs_path()}
            if cmd == "init_scripts":   return {"ok": True, "result": dcs_flash_utils.init_code_path()}
            if cmd == "migrate":        return {"ok": True, "result": data_path_utils.migrate(args[0])}
            if cmd == "recover":        return {"ok": True, "result": data_path_utils.recover(args[0])}

            if cmd == "list_serial":    return {"ok": True, "dict": scan_serial.list_serial_ports()}

            if cmd == "list_dcs":   return {"ok": True, "dict": dcs_list}
            if cmd == "rename_dcs": return {"ok": True, "result": dcs_dict_utils.rename_dcs(get_path(), args[0], args[1], dcs_list)}
            if cmd == "load_dcs":   return {"ok": True, "result": dcs_dict_utils.load_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list)}
            if cmd == "unload_dcs": return {"ok": True, "result": dcs_dict_utils.unload_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list)}
            if cmd == "delete_dcs": return {"ok": True, "result": dcs_dict_utils.delete_dcs(get_path(), args[0], dcs_list)}

        except Exception as e:
            app.logger.error(f"CMD [{cmd}] raised: {e}")
            return flask.jsonify({"ok": False, "message": f"Command failed: {e}"}), 500

    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None

    print_log.pL("Server", "Event", "Server Event: Starting on Port 5000.", "System", True, None)                       
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)     # Start the flask server

    return app                                                              # Returns the Flask Thread Created