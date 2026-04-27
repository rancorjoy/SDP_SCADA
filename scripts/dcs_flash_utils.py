# dcs_flash_utils.py
# DESCRIBE

# Import Needed Libraries
import os         # Operating System Management
import pathlib    # Object-Oriented File Path Management
import json       # JSON File Management
import shutil     # Shell Utilities (High Level File Operations)
import argparse   # Allows Console Use of Functions with Variables
import pickle     # Allows Dictionary to be saved to JSON
import subprocess # Manages Extenral Programs (eg Arduino CLI)
import sys        # Allows Python CLI Arguments to be run via code

from . import print_log

ARDUINO_CLI = "arduino-cli"                                 # Define string

# Initialize code folder inside persistent data path
def init_code_path(data_path):
    data_path = pathlib.Path(data_path)                     # Ensure data path is a path (works for path and string inputs)
    dcs_path = data_path / pathlib.Path("dcs_scripts")      # Assign dcs_path to data_path/dcs_info (name of folder)

    try:                                                    # Attempt to make folder if it does not exist
        dcs_path.mkdir(parents=True, exist_ok=True)         # parents=True creates any missing parent directories
        return True                                         # The folder was initialized
    except FileExistsError:                                 # If the folder exists and is blocking verification
        return True                                         # The folder was initialized before (just in case)
    except Exception as e:                                  # Handle other potential errors like permission issues
        print_log.pL("Flash", "Error", "An unexpected error has occured", "System", True, {e})
        return False                                        # The folder was not initialized
    
def compile_sketch(sketch_dir, fqbn):
    print_log.pL("Flash", "Event", f"Compiling Sketch.", "System", True, None)
    result = subprocess.run(
        [ARDUINO_CLI, "compile", "--fqbn", fqbn, sketch_dir],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print_log.pL("Flash", "Error", "Compilation Failed", "System", True, None)
        return False
    print_log.pL("Flash", "Event", "Compilation Sucsessful", "System", True, None)
    return True

def upload_sketch(sketch_dir, fqbn, port):
    print_log.pL("Flash", "Event", f"Uploading Sketch to {port}.", "System", True, None)
    result = subprocess.run(
        [ARDUINO_CLI, "upload", "--fqbn", fqbn, "--port", port, sketch_dir, "-v"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        print_log.pL("Flash", "Error", "Upload Failed.", "System", True, None)
        return False
    print_log.pL("Flash", "Event", "Upload Successul.", "System", True, None)
    return True

# Common Arduino VID/PID - FQBN mappings
FQBN_MAP = {
    ("0x2341", "0x0043"): "arduino:avr:uno",
    ("0x2341", "0x0001"): "arduino:avr:uno",
    ("0x2341", "0x0243"): "arduino:avr:uno",
    ("0x2341", "0x0010"): "arduino:avr:mega",
    ("0x2341", "0x0042"): "arduino:avr:mega",
    ("0x2341", "0x0036"): "arduino:avr:leonardo",
    ("0x2341", "0x8036"): "arduino:avr:leonardo",
    ("0x2341", "0x0058"): "arduino:avr:nano",
    ("0x2341", "0x8057"): "arduino:samd:mkrwifi1010",
}

def resolve_fqbn(port):
    try:
        result = subprocess.run(
            [ARDUINO_CLI, "board", "list", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print_log.pL("Flash", "Error", f"arduino-cli failed: {result.stderr.strip()}", "System", True, None)
            return None

        data = json.loads(result.stdout)

        for detected in data.get("detected_ports", []):
            port_info = detected.get("port", {})
            if port_info.get("address") == port:
                # Support both current and older arduino-cli formats
                board_list = detected.get("matching_boards") or detected.get("boards", [])
                
                if board_list:
                    fqbn = board_list[0].get("fqbn")
                    if fqbn:
                        print_log.pL("Flash", "Info", f"Detected board on {port}: {board_list[0].get('name')} → {fqbn}", "System", True, None)
                        return fqbn

                print_log.pL("Flash", "Warning", f"Port {port} found but no matching board", "System", True, None)
                return None

        print_log.pL("Flash", "Warning", f"No port matching {port} found in arduino-cli output", "System", True, None)
        return None

    except json.JSONDecodeError as e:
        print_log.pL("Flash", "Error", f"Failed to parse JSON from arduino-cli: {e}", "System", True, None)
        return None
    except Exception as e:
        print_log.pL("Flash", "Error", f"Unexpected error in resolve_fqbn: {e}", "System", True, None)
        return None

def program_controller(current_dcs, name, flash_queue, flash_lock):
    if name in current_dcs:
        with flash_lock:
            flash_queue.put({
            "port":             current_dcs[name]["port"],
            "script_name":      name
            })
            return True
    return False

