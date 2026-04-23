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
    "migrate":       (1,   1,   "migrate <relative path>"),
    "recover":       (1,   1,   "recover <relative path>"),

    "list_serial":   (0,   0,   "list_serial"),

    "list_dcs":      (0,   0,   "list_dcs"),
    "rename_dcs":    (2,   2,   "rename_dcs <old controller name> <new controller name>"),
    "unload_dcs":    (1,   1,   "unload_dcs <controller name>"),
    "load_dcs":      (1,   1,   "load_dcs <controller name>"),
    "delete_dcs":    (1,   1,   "delete_dcs <controller name>"),
    "save_dcs":      (1,   1,   "save_dcs <controller name>"),
    "reset_dcs":     (1,   1,   "reset_dcs <controller name>"),

    "list_dcs_pins":    (2,   2,    "list_dcs_pins <controller name> <bool> (active only?)"),
    "edit_pin_enable":  (3,   3,    "edit_pin_enable <controller name> <pin name> <bool> (enabled?)"),
    "edit_pin_name":    (3,   3,    "edit_pin_name <controller name> <old pin name> <new pin name>"),
    "edit_pin_type":    (3,   3,    "edit_pin_type <controller name> <pin name> <bool> (analog?)"),
    "edit_pin_dir":     (3,   3,    "edit_pin_dir <controller name> <pin name> <type> (INPUT, INPUT_PULLUP, OUTPUT)"),
    "edit_pin_pwm":     (3,   3,    "edit_pin_pwm <controller name> <pin name> <point name>"),
    "edit_pin_int":     (3,   3,    "edit_pin_int <controller name> <pin name> <bool> (interrupt enabled?)"),

    "list_dcs_points":          (1,   1,    "list_dcs_points <controller name>"),
    "add_dcs_point":            (2,   2,    "add_dcs_point <controller name> <point name>"),
    "rem_dcs_point":            (2,   2,    "rem_dcs_point <controller name> <point name>"),
    "rename_dcs_point":         (3,   3,    "rem_dcs_point <controller name> <old point name> <new point name>"),
    "edit_point_type":          (3,   3,    "edit_point_type <controller name> <point name> <type> (int, float, bool)"),
    "edit_point_def":           (3,   3,    "edit_point_def <controller name> <point name> <value>"),
    "edit_point_hold_enable":   (3,   3,    "edit_point_hold_enable <controller name> <point name> <bool> (hold point?)"),
    "edit_point_hold":          (3,   3,    "edit_point_hold <controller name> <point name> <value>"),
    "edit_point_min_enable":    (3,   3,    "edit_point_min_enable <controller name> <point name> <bool> (enforce minimum?)"),
    "edit_point_min":           (3,   3,    "edit_point_min <controller name> <point name> <value>"),
    "edit_point_max_enable":    (3,   3,    "edit_point_max_enable <controller name> <point name> <bool> (enforce maximum?)"),
    "edit_point_max":           (3,   3,    "edit_point_max <controller name> <point name> <value>"),
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
    migrate <path> :   \t Migrates the persistent data path to specified location <relative path>
    recover <path> :   \t Recovers the persistent data path at specified location <relative path>

    Serial Commands:
    list_serial : \t Lists all detected serial connections to the SCADA server

    Controller General Commands:
    list_dcs :     \t List all known DCS Controllers
    rename_dcs :   \t Rename a DCS Controller <old controller name> <new controller name>
    unload_dcs :   \t Remove a DCS from the current list <controller name>
    load_dcs :     \t Add a DCS from to current list (from file) <controller name>
    delete_dcs :   \t Delete a DCS Controller <controller name>
    save_dcs :     \t Save Changes to a DCS Controller <controller name>
    reset_dcs :    \t Undo Changes to a DCS Controller, reload from saved file <controller name>

    Controller Pin Commands:
    list_dcs_pins :     \t List all physical pins on a controller <controller name> <bool> (enabled only?)
    edit_pin_enable :   \t Enable or Disable a pin on a controller <controller name> <pin name> <bool> (enable?)
    edit_pin_name :     \t Change the name of a pin <controller name> <pin old name> <pin new name>
    edit_pin_type :     \t Change the analog behavior of a pin <controller name> <pin name> <bool> (analog?)
    edit_pin_dir :      \t Change the direction of a pin <controller name> <pin name> <type> (INPUT, INPUT_PULLUP, OUTPUT)
    edit_pin_pwm :      \t Tie the pin to output PWM from a software point <controller name> <pin name> <point name> (None to disable PWM)
    edit_pin_int:       \t Enable or Disable the ISR for this pin <controller name> <pin name> <bool> (enable?)

    Controller Point Commands:
    list_dcs_points :       \t List all enabled/active points on a controller <controller name>
    add_dcs_point :         \t Add a software point to a controller <controller name> <point name>
    rem_dcs_point :         \t Remove a software point from a controller <controller name> <point name> (this cannot be undone)
    rename_dcs_point :      \t Rename a software point on a controller <controller name> <point name>
    edit_point_type :       \t Edit the data-type stored in a point <controller name> <point name> <type> (int, float, bool)
    edit_point_def :        \t Edit the default value of a point <controller name> <point name> <value>
    edit_point_hold_enable  \t Enable or Disable point hold on a controller <controller name> <point> <bool> (hold the point?)
    edit_point_hold         \t Edit the held value of a point on a controller <controller name> <point> <value>
    edit_point_min_enable   \t Enable or Disable point minimum value on a controller <controller name> <point> <bool> (enforce minimum value?)
    edit_point_min          \t Edit the minimum value of a point on a controller <controller name> <point> <value>
    edit_point_max_enable   \t Enable or Disable point maximum value on a controller <controller name> <point> <bool> (enforce maximum value?)
    edit_point_max          \t Edit the maximum value of a point on a controller <controller name> <point> <value>
    """
    return help_text

def eval_bool(input):
    return input.lower() == "true"

def flask_loop(dcs_list, current_dict, current_dict_lock):  # Method is ran in entry point - returns "app"

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
            if cmd == "rename_dcs": return {"ok": True, "result": dcs_dict_utils.rename_dcs(get_path(), args[0], args[1], dcs_list, current_dict, current_dict_lock)}
            if cmd == "load_dcs":   return {"ok": True, "result": dcs_dict_utils.load_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list,  current_dict, current_dict_lock)}
            if cmd == "unload_dcs": return {"ok": True, "result": dcs_dict_utils.unload_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list)}
            if cmd == "delete_dcs": return {"ok": True, "result": dcs_dict_utils.delete_dcs(get_path(), args[0], dcs_list,  current_dict, current_dict_lock)}
            if cmd == "save_dcs":   return {"ok": True, "result": dcs_dict_utils.save_locked_dict(current_dict, current_dict_lock, get_path(), args[0])}
            if cmd == "reset_dcs":  return {"ok": True, "result": dcs_dict_utils.reset_locked_dict(current_dict, current_dict_lock, get_path(), args[0])}
            

            if cmd == "list_dcs_pins":      return {"ok": True, "dict": dcs_dict_utils.list_pins(current_dict[args[0]]["pin_config"],eval_bool(args[1]))}
            if cmd == "edit_pin_enable":    return {"ok": True, "result": dcs_dict_utils.change_pin_enable(current_dict[args[0]]["pin_config"],args[1], eval_bool(args[2]))}
            if cmd == "edit_pin_name":      return {"ok": True, "result": dcs_dict_utils.change_pin_name(current_dict[args[0]]["pin_config"],args[1], args[2])}
            if cmd == "edit_pin_type":      return {"ok": True, "result": dcs_dict_utils.change_pin_type(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_pin_dir":       return {"ok": True, "result": dcs_dict_utils.change_pin_dir(current_dict[args[0]]["pin_config"],args[1], args[2])}
            if cmd == "edit_pin_pwm":       return {"ok": True, "result": dcs_dict_utils.change_pin_pwm(current_dict[args[0]]["pin_config"],args[1], current_dict[args[0]]["pin_config"], args[2])}
            if cmd == "edit_pin_int":       return {"ok": True, "result": dcs_dict_utils.change_pin_int(current_dict[args[0]]["pin_config"],args[1], eval_bool(args[2]))}

            if cmd == "list_dcs_points":        return {"ok": True, "dict": dcs_dict_utils.list_points(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"])}
            if cmd == "add_dcs_point":          return {"ok": True, "result": dcs_dict_utils.add_point(current_dict[args[0]]["software_points"], args[1])}
            if cmd == "rem_dcs_point":          return {"ok": True, "result": dcs_dict_utils.rem_point(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1])}
            if cmd == "rename_dcs_point":       return {"ok": True, "result": dcs_dict_utils.change_point_name(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], args[2])}
            if cmd == "edit_point_type":        return {"ok": True, "result": dcs_dict_utils.change_point_type(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], args[2])}
            if cmd == "edit_point_def":         return {"ok": True, "result": dcs_dict_utils.change_point_def(current_dict[args[0]]["software_points"], args[1], float(args[2]))}
            if cmd == "edit_point_hold_enable": return {"ok": True, "result": dcs_dict_utils.change_point_hold_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_hold":        return {"ok": True, "result": dcs_dict_utils.change_point_hold_val(current_dict[args[0]]["software_points"], args[1], float(args[2]))}
            if cmd == "edit_point_min_enable":  return {"ok": True, "result": dcs_dict_utils.change_point_min_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_min":         return {"ok": True, "result": dcs_dict_utils.change_point_min(current_dict[args[0]]["software_points"], args[1], float(args[2]))}
            if cmd == "edit_point_max_enable":  return {"ok": True, "result": dcs_dict_utils.change_point_max_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_max":         return {"ok": True, "result": dcs_dict_utils.change_point_max(current_dict[args[0]]["software_points"], args[1], float(args[2]))}

        except Exception as e:
            app.logger.error(f"CMD [{cmd}] raised: {e}")
            return flask.jsonify({"ok": False, "message": f"Command failed: {e}"}), 500

    cli = sys.modules['flask.cli']                                          # Server Banner Suppression
    cli.show_server_banner = lambda *x: None

    print_log.pL("Server", "Event", "Server Event: Starting on Port 5000.", "System", True, None)                       
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)     # Start the flask server

    return app                                                              # Returns the Flask Thread Created