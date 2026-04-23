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
        print(f"An error occurred: {e}")                    # Print error information
        return False                                        # The folder was not initialized
    
def compile_sketch(sketch_dir, fqbn):
    print_log.pL("Flash", "Event", "Compiling Sketch {sketch_dir}.", "System", True, None)
    result = subprocess.run(
        [ARDUINO_CLI, "compile", "--fqbn", fqbn, sketch_dir],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"[!] Compilation failed:\n{result.stderr}")
        return False
    print("[+] Compilation successful.")
    return True

def upload_sketch(sketch_dir, fqbn, port):
    print_log.pL("Flash", "Event", "Uploading Sketch {sketch_dir} to {port}.", "System", True, None)
    result = subprocess.run(
        [ARDUINO_CLI, "upload", "--fqbn", fqbn, "--port", port, sketch_dir, "-v"],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode != 0:
        print_log.pL("Flash", "Error", "Uploading Failed.", "System", True, None)
        return False
    print_log.pL("Flash", "Event", "Upload Successul.", "System", True, None)
    return True

# Common Arduino VID/PID → FQBN mappings
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
    result = subprocess.run(
        [ARDUINO_CLI, "board", "list", "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    for detected in data.get("detected_ports", []):
        if detected.get("port", {}).get("address") == port:
            boards = detected.get("matching_boards", [])
            if boards:
                return boards[0]["fqbn"]
    return None



