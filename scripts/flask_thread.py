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
from dataclasses import dataclass               # Allows current state to be passed as a struct to FLASK thread

from . import data_path_utils                   # Import the data_path_utils script (current) folder
from . import dcs_dict_utils                    # Import the dcs_dict_utils script (current) folder
from . import scan_serial                       # Import the scan_serial script (current) folder
from . import dcs_flash_utils                   # Import the dcs_flash_utils script
from . import dcs_script_utils
from . import ino_utils
from . import code_block_utils
from . import print_log                
from scripts.current_state import CurrentState

logging.getLogger('werkzeug').disabled = True           # Disable default logging (reduces clutter in main window)
logging.getLogger('werkzeug.serving').disabled = True

COMMANDS = {
    #  cmd name        min  max  usage hint
    "help":                 (0,   0,   "help"),
    "status":               (0,   0,   "status"),
    "list_serial":          (0,   0,   "list_serial"),
    "list_conts":           (0,   0,   "list_conts"),
    "list_current_state":   (0,   0,   "list_current_state"),

    "init_data":     (0,   0,   "init_data"),
    "init_info":     (0,   0,   "init_info"),
    "init_scripts":  (0,   0,   "init_scripts"),
    "migrate":       (1,   1,   "migrate <relative path>"),
    "recover":       (1,   1,   "recover <relative path>"),

    "list_dcs":      (0,   0,   "list_dcs"),
    "rename_dcs":    (2,   2,   "rename_dcs <old controller name> <new controller name>"),
    "unload_dcs":    (1,   1,   "unload_dcs <controller name>"),
    "load_dcs":      (1,   1,   "load_dcs <controller name>"),
    "delete_dcs":    (1,   1,   "delete_dcs <controller name>"),
    
    "list_progs" :    (0,   0,   "list_progs"),
    "add_program" :   (0,   0,   "add_program"),
    "load_program" :  (2,   2,   "load_program <controller name> <program name>"),
    "unload_program": (2,   2,   "unload_program <controller name> <program name>"),

    "save_dcs":      (1,   1,   "save_dcs <controller name>"),
    "reset_dcs":     (1,   1,   "reset_dcs <controller name>"),
    "validate_dcs":  (1,   1,   "validate_dcs <controller name>"),
    "compile_dcs":   (1,   1,   "compile_dcs <controller name>"),
    "program_dcs":   (1,   1,   "program_dcs <controller name>"),

    "list_dcs_pins":    (2,   2,    "list_dcs_pins <controller name> <bool> (active only?)"),
    "edit_pin_enable":  (3,   3,    "edit_pin_enable <controller name> <pin name> <bool> (enabled?)"),
    "edit_pin_name":    (3,   3,    "edit_pin_name <controller name> <old pin name> <new pin name>"),
    "edit_pin_type":    (3,   3,    "edit_pin_type <controller name> <pin name> <bool> (analog?)"),
    "edit_pin_dir":     (3,   3,    "edit_pin_dir <controller name> <pin name> <type> (INPUT, INPUT_PULLUP, OUTPUT)"),
    "edit_pin_pwm":     (3,   3,    "edit_pin_pwm <controller name> <pin name> <bool> (enable PWM?)"),
    "edit_pin_int":     (3,   3,    "edit_pin_int <controller name> <pin name> <bool> (interrupt enabled?)"),

    "list_dcs_points":          (1,   1,    "list_dcs_points <controller name>"),
    "list_integer_types":       (0,   0,    "list_integer_types"),
    "add_dcs_point":            (2,   2,    "add_dcs_point <controller name> <point name>"),
    "rem_dcs_point":            (2,   2,    "rem_dcs_point <controller name> <point name>"),
    "rename_dcs_point":         (3,   3,    "rem_dcs_point <controller name> <old point name> <new point name>"),
    "edit_point_type":          (3,   3,    "edit_point_type <controller name> <point name> <type> (int, float, bool)"),
    "edit_point_spec_type":     (3,   3,    "edit_point_spec_type <controller name> <point name> <type> (eg long long int or double float)"),
    "edit_point_def":           (3,   3,    "edit_point_def <controller name> <point name> <value>"),
    "edit_point_const":         (3,   3,    "edit_point_const <controller name> <point name> <value>"),
    "edit_point_hold_enable":   (3,   3,    "edit_point_hold_enable <controller name> <point name> <bool> (hold point?)"),
    "edit_point_hold":          (3,   3,    "edit_point_hold <controller name> <point name> <value>"),
    "edit_point_min_enable":    (3,   3,    "edit_point_min_enable <controller name> <point name> <bool> (enforce minimum?)"),
    "edit_point_min":           (3,   3,    "edit_point_min <controller name> <point name> <value>"),
    "edit_point_max_enable":    (3,   3,    "edit_point_max_enable <controller name> <point name> <bool> (enforce maximum?)"),
    "edit_point_max":           (3,   3,    "edit_point_max <controller name> <point name> <value>"),

    "list_dcs_timers":          (1,   1,    "list_dcs_timers <controller name>"),
    "edit_timer_enable":        (3,   3,    "edit_timer_enable <controller name> <point name> <value> (enabled?)"),
    "edit_timer_mode":          (3,   3,    "edit_timer_mode <controller name> <point name> <mode> (See Arduino manual for timer operating modes)"),
    "list_dcs_interrupts":      (1,   1,    "list_dcs_interrupts <controller name>"),
    "edit_int_enable":          (3,   3,    "edit_int_enable <controller name> <point name> <value> (enabled?)"),
    "edit_int_mode":            (3,   3,    "edit_int_mode <controller name> <point name> <mode> (Pin: LOW, CHANGE, RISING, FALLING, HIGH; Timer: OVF, MATCH)"),

    "list_dcs_arrays":          (1,   1,    "list_dcs_arrays <controller name>"),
    "add_array":                (2,   2,    "add_array <controller name> <array name>"),
    "rem_array":                (2,   2,    "rem_array <controller name> <array name>"),
    "rename_array":             (3,   3,    "rename_array <controller name> <old array name> <new array name>"),
    "add_array_const":          (3,   3,    "add_array_const <controller name> <array name> <software point>"),
    "rem_array_const":          (2,   2,    "rem_array_const <controller name> <array name>"),

    "list_dcs_blk_lists" :      (1,   1,    "list_dcs_blk_lists <controller name>"),
    "add_block_top":            (3,   3,    "add_block_top <controller name> <list name> <block type>"),
    "add_block_bottom":         (3,   3,    "add_block_bottom <controller name> <list name> <block type>"),
    "add_block_index":          (4,   4,    "add_block_index <controller name> <list name> <block type> <index>"),
    "move_block_up" :           (3,   3,    "move_block_up <controller name> <list name> <index>"),
    "move_block_down" :         (3,   3,    "move_block_down <controller name> <list name> <index>"),
    "swap_blocks" :             (4,   4,    "swap_blocks <controller name> <list name> <index1> <index2>"),
    "remove_block" :            (3,   3,    "remove_block <controller name> <list name> <index>"),

    "add_input_point" :         (5,   5,    "add_input_point <controller name> <list name> <index> <key> <point>"),
    "add_input_array" :         (5,   5,    "add_input_array <controller name> <list name> <index> <key> <array>"),
    "rem_input_point" :         (4,   4,    "rem_input_point <controller name> <list name> <index> <key>"),
    "add_output_point" :        (5,   5,    "add_output_point <controller name> <list name> <index> <key> <point>"),
    "add_output_array" :        (5,   5,    "add_input_array <controller name> <list name> <index> <key> <array>"),
    "rem_output_point" :        (4,   4,    "rem_output_point <controller name> <list name> <index> <key>"),

    "list_block_types" :        (0,   0,    "list_block_types"),
    "current_block_config" :    (1,   1,    "current_block_config <controller name>"),
    "saved_block_config" :      (1,   1,    "saved_block_config <controller name>"),
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
    help :              \t Displays a list of all valid commands
    status :            \t Displays the network status of the SCADA server
    list_serial :       \t Lists all detected serial connections to the SCADA server
    list_conts :        \t List all saved controllers
    list_current_state :\t Lists current state of SCADA system (all loaded control info)

    Data Path Commands:
    init_data :        \t Initializes the persistent data path
    init_info :        \t Initializes the dcs information folder
    init_scripts :     \t Initializes the dcs scripts folder
    migrate <path> :   \t Migrates the persistent data path to specified location <relative path>
    recover <path> :   \t Recovers the persistent data path at specified location <relative path>

    Controller General Commands:
    list_dcs :     \t List all connected DCS Controllers
    rename_dcs :   \t Rename a DCS Controller or program <old controller name> <new controller name>
    unload_dcs :   \t Remove a DCS from the current list <controller name>
    load_dcs :     \t Add a DCS from to current list (from file) <controller name>
    delete_dcs :   \t Delete a DCS Controller or program <controller/program name>

    Controller Program Commands:
    list_progs :    \t List all saved programs (not inclusing connected DCS controllers)
    add_program :   \t Create a new program
    load_program:   \t Load a saved program into a Controller's current state <controller name> <current name>
    unload_program: \t Load a Controller's saved state into a program's current state <controller name> <current name>

    Controlller Program Pipeline Commands:
    save_dcs :     \t Save Changes to a DCS Controller or program <controller name>
    reset_dcs :    \t Undo Changes to a DCS Controller or program, reload from saved file <controller name>
    compile_dcs :  \t Validate controller configuration based on coding rules <controller name>
    compile_dcs :  \t Regenerate code for a DCS Controller based on saved state if valid <controller name>
    program_dcs :  \t Reprogram a DCS Controller based on generated code <controller name>

    Controller Pin Commands:
    list_dcs_pins :     \t List all physical pins on a controller <controller name> <bool> (enabled only?)
    edit_pin_enable :   \t Enable or Disable a pin on a controller <controller name> <pin name> <bool> (enable?)
    edit_pin_name :     \t Change the name of a pin <controller name> <pin old name> <pin new name>
    edit_pin_type :     \t Change the analog behavior of a pin <controller name> <pin name> <bool> (analog?)
    edit_pin_dir :      \t Change the direction of a pin <controller name> <pin name> <type> (INPUT, INPUT_PULLUP, OUTPUT)
    edit_pin_pwm :      \t Set a pin to output PWM (will set pin as OUTPUT, int) <controller name> <pin name> <bool> (enable PWM?)
    edit_pin_int:       \t Enable or Disable the ISR for this pin <controller name> <pin name> <bool> (enable?)

    Controller Point Commands:
    list_integer_types :    \t List the types of valid integer assignments in C++ (for special type assignment)
    list_dcs_points :       \t List all enabled/active points on a controller <controller name>
    add_dcs_point :         \t Add a software point to a controller <controller name> <point name>
    rem_dcs_point :         \t Remove a software point from a controller <controller name> <point name> (this cannot be undone)
    rename_dcs_point :      \t Rename a software point on a controller <controller name> <point name>
    edit_point_type :       \t Edit the data-type stored in a point <controller name> <point name> <type> (int, float, bool)
    edit_point_spec_type :  \t Edit the data-type stored in a point <controller name> <point name> <type> (eg long long unsigned int) for an int or float. None for default type,
    edit_point_def :        \t Edit the default value of a point <controller name> <point name> <value>
    edit_point_const :      \t Edit the constant value of a point <controller name> <point name> <value> (false by default, is the point a constant?)
    edit_point_hold_enable  \t Enable or Disable point hold on a controller <controller name> <point> <bool> (hold the point?)
    edit_point_hold         \t Edit the held value of a point on a controller <controller name> <point> <value>
    edit_point_min_enable   \t Enable or Disable point minimum value on a controller <controller name> <point> <bool> (enforce minimum value?)
    edit_point_min          \t Edit the minimum value of a point on a controller <controller name> <point> <value>
    edit_point_max_enable   \t Enable or Disable point maximum value on a controller <controller name> <point> <bool> (enforce maximum value?)
    edit_point_max          \t Edit the maximum value of a point on a controller <controller name> <point> <value>

    Timer and Interrupt Commands:
    list_dcs_timers :       \t List all timers on a controller <controller name>
    edit_timer_enable :     \t Enable or Disable a timer on a controller <controller name> <point name> <value> (enabled?)
    edit_timer_mode :       \t Change the mode of a timer on a controller <controller name> <point name> <mode> (8-bit: OVF, CTC, FAST_PWM, PHASE_CORRECT_PWM ; 16-bit: INPUT_CAPTURE)
    list_dcs_interrupt :    \t List all interrupts on a controller <controller name>
    edit_int_enable :       \t Enable or Disable an interrupt on a controller <controller name> <point name> <value> (enabled?)
    edit_int_mode :         \t Change the mode of an interrupt on a controller <controller name> <point name> <mode> (LOW, CHANGE, RISING, FALLING, HIGH)

    Array Commands:     
    add_array :             \t Add an array to a controller <controller name> <array name>
    rem_array :             \t Remove an array from a controller <controller name> <array name>
    rename_array :          \t Rename an array in a controller <controller name> <old array name> <new array name>
    add_array_const :       \t Add the constant point to an array to determine its size <controller name> <array name> <point name>
    rem_array_const :       \t Remove the constant point from an array <controller name> <array name>

    Code Block Commands:
    list_dcs_blk_lists :      \t List all current block lists for a controller <controller name>
    add_block_top :           \t Add a code block to top of a block list <controller name> <list name> <block type>
    add_block_bottom :        \t Add a code block to bottom of a block list <controller name> <list name> <block type>
    add_block_index :         \t Add a code block to index position of block list <controller name> <list name> <block type> <index>
    move_block_up :           \t Move a block up in a block list <controller name> <list name> <index>
    move_block_down :         \t Move a block down in a block list <controller name> <list name> <index>
    swap_blocks :             \t Swap two blocks in a block list <controller name> <list name> <index1> <index2>
    remove_block :            \t Remove a block from a block list <controller name> <list name> <index>

    Code Block Point Commands:
    add_input_point :         \t Add a point to block input (key) <controller name> <list name> <index> <key> <point>
    add_input_array :         \t Add a array to block input (key) <controller name> <list name> <index> <key> <point>
    rem_input_point :         \t Remove a point/array from block input (key) <controller name> <list name> <index> <key>
    add_output_point :        \t Add a point to block output (key) <controller name> <list name> <index> <key> <point>
    add_output_array :        \t Add a array to block output (key) <controller name> <list name> <index> <key> <point>
    rem_output_point :        \t Remove a point/array from block output (key) <controller name> <list name> <index> <key>

    Code Block Utility Commands:
    list_block_types :        \t List all available block types and details
    current_block_config :    \t See block order in each list (current state) <controller name>
    saved_block_config :      \t See block order in each list (saved state) <controller name>
    """
    return help_text

def eval_bool(input):
    return input.lower() == "true"

def split_dcs_list(dcs_list):
    cont_list = {}
    prog_list = {}
    for key in dcs_list:
        if dcs_dict_utils.is_prog(dcs_list[key]):
            prog_list[key] = dcs_list[key]
        else:
            cont_list[key] = dcs_list[key]
    return cont_list, prog_list

def flask_loop(CurrentState):                               # Method is ran in entry point - returns "app"

    # Get data objects out of current state
    dcs_list = CurrentState.current_dcs
    current_dict = CurrentState.current_dict
    current_dict_lock = CurrentState.current_dict_lock
    flash_queue = CurrentState.flash_queue
    flash_lock = CurrentState.flash_lock
    block_lib = CurrentState.block_lib

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
            if cmd == "help":               return {"ok": True, "message": get_help()}
            if cmd == "status":             return {"ok": True, "message": "Running"}
            if cmd == "list_serial":        return {"ok": True, "dict": scan_serial.list_serial_ports()}
            if cmd == "list_conts":         return {"ok": True, "dict": split_dcs_list(current_dict)[0]}
            if cmd == "list_current_state": return {"ok": True, "dict": current_dict}

            if cmd == "init_data":      return {"ok": True, "result": data_path_utils.init_data_path()}
            if cmd == "init_info":      return {"ok": True, "result": dcs_dict_utils.init_dcs_path()}
            if cmd == "init_scripts":   return {"ok": True, "result": dcs_flash_utils.init_code_path()}
            if cmd == "migrate":        return {"ok": True, "result": data_path_utils.migrate(args[0])}
            if cmd == "recover":        return {"ok": True, "result": data_path_utils.recover(args[0])}

            if cmd == "list_dcs":   return {"ok": True, "dict": dcs_list}
            if cmd == "rename_dcs": return {"ok": True, "result": dcs_dict_utils.rename_dcs(get_path(), args[0], args[1], dcs_list, current_dict, current_dict_lock)}
            if cmd == "load_dcs":   return {"ok": True, "result": dcs_dict_utils.load_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list,  current_dict, current_dict_lock)}
            if cmd == "unload_dcs": return {"ok": True, "result": dcs_dict_utils.unload_dcs(get_path(), dcs_dict_utils.name_to_port(get_path(), args[0]), dcs_list)}
            if cmd == "delete_dcs": return {"ok": True, "result": dcs_dict_utils.delete_dcs(get_path(), args[0], dcs_list,  current_dict, current_dict_lock)}
            
            if cmd == "list_progs":         return {"ok": True, "dict": split_dcs_list(current_dict)[1]}
            if cmd == "add_program" :       return {"ok": True, "result": dcs_dict_utils.init_code_dcs(get_path(), current_dict, current_dict_lock)}
            if cmd == "load_program" :      return {"ok": True, "result": dcs_dict_utils.load_prog_to_cont(args[0], args[1], current_dict, get_path())}
            if cmd == "unload_program" :    return {"ok": True, "result": dcs_dict_utils.load_cont_to_prog(get_path(), args[0], current_dict, args[1])}

            if cmd == "save_dcs":       return {"ok": True, "result": dcs_dict_utils.save_locked_dict(current_dict, current_dict_lock, get_path(), args[0])}
            if cmd == "reset_dcs":      return {"ok": True, "result": dcs_dict_utils.reset_locked_dict(current_dict, current_dict_lock, get_path(), args[0])}
            if cmd == "validate_dcs":   return {"ok": True, "message": code_block_utils.print_validation(get_path(), args[0], block_lib)}
            if cmd == "compile_dcs":    return {"ok": True, "result": code_block_utils.check_compile(get_path(), args[0], block_lib, current_dict)}
            if cmd == "program_dcs":    return {"ok": True, "result": dcs_flash_utils.program_controller(dcs_list, args[0], flash_queue, flash_lock)}
            

            if cmd == "list_dcs_pins":      return {"ok": True, "dict": dcs_dict_utils.list_pins(current_dict[args[0]]["pin_config"],eval_bool(args[1]))}
            if cmd == "edit_pin_enable":    return {"ok": True, "result": dcs_dict_utils.change_pin_enable(current_dict[args[0]]["pin_config"],args[1], eval_bool(args[2]))}
            if cmd == "edit_pin_name":      return {"ok": True, "result": dcs_dict_utils.change_pin_name(current_dict[args[0]]["pin_config"],args[1], args[2])}
            if cmd == "edit_pin_type":      return {"ok": True, "result": dcs_dict_utils.change_pin_type(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_pin_dir":       return {"ok": True, "result": dcs_dict_utils.change_pin_dir(current_dict[args[0]]["pin_config"],args[1], args[2])}
            if cmd == "edit_pin_pwm":       return {"ok": True, "result": dcs_dict_utils.change_pin_pwm(current_dict[args[0]]["pin_config"],args[1], current_dict[args[0]]["software_points"], args[2])}
            if cmd == "edit_pin_int":       return {"ok": True, "result": dcs_dict_utils.change_pin_int(current_dict[args[0]]["pin_config"],args[1], eval_bool(args[2]))}

            if cmd == "list_integer_types":     return {"ok": True, "message": dcs_dict_utils.show_int_types()}
            if cmd == "list_dcs_points":        return {"ok": True, "dict": dcs_dict_utils.list_points(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], current_dict[args[0]]["timers"])}
            if cmd == "add_dcs_point":          return {"ok": True, "result": dcs_dict_utils.add_point(current_dict[args[0]]["software_points"], args[1])}
            if cmd == "rem_dcs_point":          return {"ok": True, "result": dcs_dict_utils.rem_point(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1])}
            if cmd == "rename_dcs_point":       return {"ok": True, "result": dcs_dict_utils.change_point_name(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], args[2])}
            if cmd == "edit_point_type":        return {"ok": True, "result": dcs_dict_utils.change_point_type(current_dict[args[0]]["pin_config"], current_dict[args[0]]["software_points"], args[1], args[2], False)}
            if cmd == "edit_point_spec_type":   return {"ok": True, "result": dcs_dict_utils.change_point_spec_type(current_dict[args[0]]["software_points"], args[1], args[2])}
            if cmd == "edit_point_def":         return {"ok": True, "result": dcs_dict_utils.change_point_def(current_dict[args[0]]["software_points"], args[1], float(args[2]), current_dict[args[0]]["timers"])}
            if cmd == "edit_point_const":       return {"ok": True, "result": dcs_dict_utils.change_point_const(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]), current_dict[args[0]]["arrays"])}
            if cmd == "edit_point_hold_enable": return {"ok": True, "result": dcs_dict_utils.change_point_hold_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_hold":        return {"ok": True, "result": dcs_dict_utils.change_point_hold_val(current_dict[args[0]]["software_points"], args[1], float(args[2]), current_dict[args[0]]["timers"])}
            if cmd == "edit_point_min_enable":  return {"ok": True, "result": dcs_dict_utils.change_point_min_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_min":         return {"ok": True, "result": dcs_dict_utils.change_point_min(current_dict[args[0]]["software_points"], args[1], float(args[2]), current_dict[args[0]]["timers"])}
            if cmd == "edit_point_max_enable":  return {"ok": True, "result": dcs_dict_utils.change_point_max_en(current_dict[args[0]]["software_points"], args[1], eval_bool(args[2]))}
            if cmd == "edit_point_max":         return {"ok": True, "result": dcs_dict_utils.change_point_max(current_dict[args[0]]["software_points"], args[1], float(args[2]), current_dict[args[0]]["timers"])}

            if cmd == "list_dcs_timers":        return {"ok": True, "dict": current_dict[args[0]]["timers"]}
            if cmd == "edit_timer_enable":      return {"ok": True, "result": dcs_dict_utils.set_timer_enable(current_dict[args[0]]["timers"], args[1], eval_bool(args[2]), current_dict[args[0]]["int_config"])}
            if cmd == "edit_timer_mode":        return {"ok": True, "result": dcs_dict_utils.set_timer_mode(current_dict[args[0]]["timers"], args[1], args[2], current_dict[args[0]]["int_config"])}
            if cmd == "list_dcs_interrupts":    return {"ok": True, "dict": current_dict[args[0]]["int_config"]}
            if cmd == "edit_int_enable":        return {"ok": True, "result": dcs_dict_utils.set_int_enable(current_dict[args[0]]["int_config"], args[1], eval_bool(args[2]))}
            if cmd == "edit_int_mode":          return {"ok": True, "result": dcs_dict_utils.set_int_mode(current_dict[args[0]]["int_config"], args[1], args[2])}

            if cmd == "list_dcs_arrays":        return {"ok": True, "dict": current_dict[args[0]]["arrays"]}
            if cmd == "add_array":              return {"ok": True, "result": dcs_dict_utils.add_array(current_dict[args[0]]["arrays"], args[1])}
            if cmd == "rem_array":              return {"ok": True, "result": dcs_dict_utils.rem_array(current_dict[args[0]]["arrays"], args[1])}
            if cmd == "rename_array":           return {"ok": True, "result": dcs_dict_utils.ren_array(current_dict[args[0]]["arrays"], args[1], args[2])}
            if cmd == "add_array_const":        return {"ok": True, "result": dcs_dict_utils.add_array_const(current_dict[args[0]]["arrays"], args[1],current_dict[args[0]]["software_points"], args[2])}
            if cmd == "rem_array_const":        return {"ok": True, "result": dcs_dict_utils.rem_array(current_dict[args[0]]["arrays"], args[1])}

            if cmd == "list_dcs_blk_lists":     return {"ok": True, "message": code_block_utils.display_lists(current_dict, args[0])}
            if cmd == "add_block_top":          return {"ok": True, "result": code_block_utils.add_block_top(current_dict, args[0], args[1], args[2], block_lib)}
            if cmd == "add_block_bottom":       return {"ok": True, "result": code_block_utils.add_block_bot(current_dict, args[0], args[1], args[2], block_lib)}
            if cmd == "add_block_index":        return {"ok": True, "result": code_block_utils.add_block_index(current_dict, args[0], args[1], args[2], int(args[3]), block_lib)}
            if cmd == "move_block_up":          return {"ok": True, "result": code_block_utils.block_list_move_up(current_dict, args[0], args[1], int(args[2]))}
            if cmd == "move_block_down":        return {"ok": True, "result": code_block_utils.block_list_move_down(current_dict, args[0], args[1], int(args[2]))}
            if cmd == "swap_blocks":            return {"ok": True, "result": code_block_utils.block_list_swap(current_dict, args[0], args[1], int(args[2]), int(args[3]))}
            if cmd == "remove_block":           return {"ok": True, "result": code_block_utils.remove_block_index(current_dict, args[0], args[1], int(args[2]))}

            if cmd == "add_input_point":        return {"ok": True, "result": code_block_utils.add_point_input(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3], current_dict[args[0]]["software_points"][args[4]], block_lib, current_dict[args[0]]["software_points"])}
            if cmd == "add_input_array":        return {"ok": True, "result": code_block_utils.add_array_input(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3], current_dict[args[0]]["arrays"][args[4]], block_lib, current_dict[args[0]]["arrays"])}
            if cmd == "rem_input_point":        return {"ok": True, "result": code_block_utils.remove_point_input(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3])}
            if cmd == "add_output_point":       return {"ok": True, "result": code_block_utils.add_point_output(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3], current_dict[args[0]]["software_points"][args[4]], block_lib, current_dict[args[0]]["software_points"])}
            if cmd == "add_output_array":       return {"ok": True, "result": code_block_utils.add_array_output(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3], current_dict[args[0]]["arrays"][args[4]], block_lib, current_dict[args[0]]["arrays"])}
            if cmd == "rem_output_point":       return {"ok": True, "result": code_block_utils.remove_point_output(code_block_utils.get_inst(current_dict, args[0], args[1], int(args[2])), args[3])}

            if cmd == "list_block_types":     return {"ok": True, "message": code_block_utils.display_block_help(block_lib)}  # already correct
            if cmd == "current_block_config": return {"ok": True, "message": code_block_utils.display_current_config(current_dict, args[0], block_lib)}
            if cmd == "saved_block_config":   return {"ok": True, "message": code_block_utils.display_saved_config(get_path(), args[0], block_lib)}

        except Exception as e:
            app.logger.error(f"CMD [{cmd}] raised: {e}")
            return flask.jsonify({"ok": False, "message": f"Command failed: {e}"}), 500

    cli = sys.modules['flask.cli']                                          # Server Banner Suppression
    cli.show_server_banner = lambda *x: None

    print_log.pL("Server", "Event", "Server Event: Starting on Port 5000.", "System", True, None)                       
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)     # Start the flask server

    return app                                                              # Returns the Flask Thread Created