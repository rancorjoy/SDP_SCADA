# dcs_flash_thread.py
# DESCRIBE

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON
import threading    # Multithreading for Commands Outside of Loop

from . import dcs_flash_utils                               # Import the dcs_flash_utils script (current) folder

flash_locks = {}                                            # Port -> Lock mapping

# Constantly running loop that checks for queued flash calls and flashes controllers when queued
def flash_loop(event_queue, datapath, is_init):

    data_path = pathlib.Path(datapath)                      # Ensure data path is a path (works for path and string inputs)
    code_path = data_path / pathlib.Path("dcs_scripts")     # Assign dcs_path to data_path/dcs_scripts (name of folder)

    if(is_init):                                            # If the scripts folder exists and has been initialized
        while True:
            event = event_queue.get()

            port        = event["port"]
            script_name = event["script_name"]
            fqbn = dcs_flash_utils.resolve_fqbn(port)
            if fqbn is None:
                print(f"[!] Could not detect board type on {port}, aborting.")
                event_queue.task_done()
                continue

            if port not in flash_locks:                     # Create a lock for this port if one doesn't exist
                flash_locks[port] = threading.Lock()

            if flash_locks[port].locked():                  # If this port is already being flashed, skip
                print(f"[!] Flash already in progress on {port}, skipping.")
                event_queue.task_done()
                continue

            ino_path = code_path / pathlib.Path(script_name)
            if not ino_path.exists():
                print(f"[!] Script not found: {ino_path}")
                event_queue.task_done()
                continue

            with flash_locks[port]:
                dcs_flash_utils.compile_sketch(ino_path, fqbn)                        # pass path, not code
                dcs_flash_utils.upload_sketch(ino_path, fqbn, port)                   # pass path, not code

            event_queue.task_done()

    return