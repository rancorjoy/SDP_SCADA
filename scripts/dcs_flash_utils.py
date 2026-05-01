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
import time       # For retry sleep
import serial.tools.list_ports  # For VID/PID fallback without opening the port

from . import dcs_dict_utils
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
# Keys are (hex_vid_str, hex_pid_str) matching the output of hex() on pyserial integers
FQBN_MAP = {
    ("0x2341", "0x43"):   "arduino:avr:uno",       # hex() omits leading zeros, e.g. 0x0043 -> "0x43"
    ("0x2341", "0x1"):    "arduino:avr:uno",
    ("0x2341", "0x243"):  "arduino:avr:uno",
    ("0x2341", "0x10"):   "arduino:avr:mega",
    ("0x2341", "0x42"):   "arduino:avr:mega",
    ("0x2341", "0x36"):   "arduino:avr:leonardo",
    ("0x2341", "0x8036"): "arduino:avr:leonardo",
    ("0x2341", "0x58"):   "arduino:avr:nano",
    ("0x2341", "0x8057"): "arduino:samd:mkrwifi1010",
}

def _fqbn_from_pyserial(port):
    """
    Read VID/PID directly from pyserial (reads sysfs on Linux, no port open needed).
    Returns fqbn string or None.
    """
    for p in serial.tools.list_ports.comports():
        if p.device == port:
            if p.vid is not None and p.pid is not None:
                vid_str = hex(p.vid)   # e.g. "0x2341"
                pid_str = hex(p.pid)   # e.g. "0x43"  (no zero-padding)
                fqbn = FQBN_MAP.get((vid_str, pid_str))
                if fqbn:
                    print_log.pL("Flash", "Event", f"Resolved board on {port} via VID/PID {vid_str}:{pid_str} → {fqbn}", "System", True, None)
                else:
                    print_log.pL("Flash", "Error", f"Port {port} found, VID/PID {vid_str}:{pid_str} not in FQBN_MAP", "System", True, None)
                return fqbn
    print_log.pL("Flash", "Error", f"Port {port} not found by pyserial comports()", "System", True, None)
    return None

def _fqbn_from_arduino_cli(port):
    """
    Ask arduino-cli to identify the board. Returns fqbn string or None.
    Does NOT retry - caller handles retries.
    """
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
                board_list = detected.get("matching_boards") or detected.get("boards", [])
                if board_list:
                    fqbn = board_list[0].get("fqbn")
                    if fqbn:
                        print_log.pL("Flash", "Event", f"arduino-cli detected board on {port}: {board_list[0].get('name')} → {fqbn}", "System", True, None)
                        return fqbn
                # Port found but arduino-cli couldn't identify it - fall through to None
                return None

        return None  # Port not listed at all yet

    except json.JSONDecodeError as e:
        print_log.pL("Flash", "Error", f"Failed to parse JSON from arduino-cli: {e}", "System", True, None)
        return None
    except Exception as e:
        print_log.pL("Flash", "Error", f"Unexpected error in arduino-cli call: {e}", "System", True, None)
        return None

def resolve_fqbn(port, retries=5, delay=1.0):
    """
    Resolve the FQBN for the Arduino on the given port.

    Strategy:
      1. Try pyserial VID/PID lookup first - fast, works without port open, reliable on Pi.
      2. If that fails, retry arduino-cli board list up to `retries` times with `delay` seconds
         between attempts. On Linux the port may still be releasing after the worker closed it,
         so arduino-cli may not see it on the first try.

    Args:
        port:    Serial port path, e.g. "/dev/ttyACM0"
        retries: How many times to attempt arduino-cli detection (default 5)
        delay:   Seconds to wait between arduino-cli attempts (default 1.0)
    """

    # --- Step 1: pyserial VID/PID (fast, no port open, reads sysfs directly on Linux) ---
    fqbn = _fqbn_from_pyserial(port)
    if fqbn:
        return fqbn

    print_log.pL("Flash", "Event", f"pyserial VID/PID lookup failed for {port}, falling back to arduino-cli with {retries} retries...", "System", True, None)

    # --- Step 2: arduino-cli with retry loop ---
    # On Pi, the port may still be held by the OS briefly after the worker closes it.
    # arduino-cli won't list a port it can't probe, so we retry with a delay.
    for attempt in range(1, retries + 1):
        print_log.pL("Flash", "Event", f"arduino-cli board detect attempt {attempt}/{retries} for {port}", "System", True, None)
        fqbn = _fqbn_from_arduino_cli(port)
        if fqbn:
            return fqbn
        if attempt < retries:
            time.sleep(delay)

    print_log.pL("Flash", "Error", f"Could not resolve FQBN for {port} after pyserial + {retries} arduino-cli attempts.", "System", True, None)
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