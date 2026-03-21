# Import Needed Libraries
import os           # Operating System Management
import time         # Time Keeping and Sleep
import pathlib      # Object-Oriented File Path Management
import json         # JSON File Management
import shutil       # Shell Utilities (High Level File Operations)
import threading    # Multithreading for Commands Outside of Loop
import flask        # Lightweight web server
import requests     # For Command Line Interface Window
import serial                   # Serial Communications over USB<->USB
import serial.tools.list_ports  # Serial communication tools for port detection
import queue                    # Adds queues that can be pushed or popped to from a thread

# Import the scripts folder - scripts and utility methods
from scripts import data_path_utils
from scripts import dcs_dict_utils
from scripts import flask_thread
from scripts import serial_thread

def main():                                         # Main Method - Program Entry Point
    
                                                    # Initialize Data Path and Sub-Paths
    is_path = data_path_utils.init_data_path()      # Initialize Data Path
    path = data_path_utils.get_data_path()          # Get Current Data Path
    is_info = dcs_dict_utils.init_dcs_path(path)    # Initialize DCS Info Path

    event_queue = queue.Queue()                 # Create an event queue for the serial monitoring thread
    
                                                # Create a thread that runs serial_thread.serial_loop
                                                # Pass the thread the event queue so results can be used in main thread
    monitor_thread = threading.Thread(target=serial_thread.serial_loop, args=(event_queue,))
    monitor_thread.daemon = True                # Dies when main program dies
    monitor_thread.start()                      # Start the new thread

                                                # Start HTTP server in background thread
    app = flask_thread.flask_loop()             # Initialize Flask Application
    thread = threading.Thread(target=app.run)   # Make a new thread
    thread.daemon = True                        # Dies when main program dies
    thread.start()                              # Start the new thread

    current_dcs = {}

    devices = {}
    previous_devices = {}

    while True:                                 # Main Loop
        
        time.sleep(1)                           # Wait 1 Second - Temporary Logic
        print("Main Loop")                      # Print "Main Loop" - Temporary Logic

                                                # Non-blocking check for new serial events
        while not event_queue.empty():          # Whenever the event queue is not empty...
            event = event_queue.get()           # Get the current state of the event queue from the serial thread
            print(f"Serial event: {event}")     # Print detection of connection or disconnection
                                                # If a serial event has been detected... update device list:
            
            previous_devices = dict(devices)

            with serial_thread.devices_lock:                    # Lock while reading
                devices = dict(serial_thread.connected_devices) # Get list of all devices from the serial thread dictionary
                
                # Newly connected devices
                for device in devices.values():
                    if device not in previous_devices.values():
                        is_saved = dcs_dict_utils.init_dcs(path, device)
                    if is_saved:
                        is_loaded = dcs_dict_utils.load_dcs(path, device, current_dcs)

                # Disconnected devices
                for device in previous_devices.values():
                    if device not in devices.values():
                        is_removed = dcs_dict_utils.unload_dcs(path, device, current_dcs)

                print(current_dcs)

main()  # Run Main Loop
