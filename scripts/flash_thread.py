# dcs_flash_thread.py
# DESCRIBE

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle       # Allows Dictionary to be saved to JSON
import threading    # Multithreading for Commands Outside of Loop
import time

from . import dcs_flash_utils                               # Import the dcs_flash_utils script (current) folder
from . import print_log

flash_locks = {}                                            # Port -> Lock mapping

# Constantly running loop that checks for queued flash calls and flashes controllers when queued
def flash_loop(event_queue, lock, datapath, is_init, worker_threads):

    data_path = pathlib.Path(datapath)                      # Ensure data path is a path (works for path and string inputs)
    code_path = data_path / pathlib.Path("dcs_scripts")     # Assign dcs_path to data_path/dcs_scripts (name of folder)

    if(is_init):                                            # If the scripts folder exists and has been initialized
            while True:
                event = event_queue.get()                   # If a command is recieved...
                port        = event["port"]
                script_name = event["script_name"]
                
                # send a pause event with a ready event attached
                pause_event = threading.Event()
                worker_threads[port]["cmd_queue"].put({"command": "pause", "ready": pause_event})
                pause_event.wait()  # block flash thread until port is actually closed
                time.sleep(0.1)

                fqbn = dcs_flash_utils.resolve_fqbn(port)

                if fqbn is None:
                    print_log.pL("Flash", "Error", f"Could not detect board type on {port}, aborting.", "System", True, None)
                    with lock:
                        event_queue.task_done()
                        worker_threads[port]["cmd_queue"].put({"command": "continue"})
                    continue
                
                if port not in flash_locks:
                    flash_locks[port] = threading.Lock()

                if flash_locks[port].locked():                  # If this port is already being flashed, skip
                    print_log.pL("Flash", "Error", f"Flash already in progress on {port}, skipping.", "System", True, None)
                    with lock:
                        event_queue.task_done()
                        worker_threads[port]["cmd_queue"].put({"command": "continue"})
                    continue

                ino_path = code_path / pathlib.Path(script_name)
                if not ino_path.exists():
                    print_log.pL("Flash", "Error", f"Script {script_name} not found", "System", True, None)
                    with lock:
                        event_queue.task_done()
                        worker_threads[port]["cmd_queue"].put({"command": "continue"})
                    continue

                with flash_locks[port]:
                    if dcs_flash_utils.compile_sketch(ino_path, fqbn):
                        dcs_flash_utils.upload_sketch(ino_path, fqbn, port)
                    else:
                        print_log.pL("Flash", "Error", f"Skipping upload for {port} due to compile failure.", "System", True, None)

                with lock:
                    event_queue.task_done()
                    worker_threads[port]["cmd_queue"].put({"command": "continue"})

    return