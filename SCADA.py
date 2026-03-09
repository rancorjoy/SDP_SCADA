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

# Import the scripts folder
from scripts import data_path_utils
from scripts import flask_thread
from scripts import serial_thread

def main():                                     # Main Method - Program Entry Point
    path = data_path_utils.init_data_path()     # Initialize Data Path


    event_queue = queue.Queue()
    
    monitor_thread = threading.Thread(target=serial_thread.serial_loop, args=(event_queue,))
    monitor_thread.daemon = True
    monitor_thread.start()

                                                # Start HTTP server in background thread
    app = flask_thread.flask_loop()             # Initialize Flask Application
    thread = threading.Thread(target=app.run)   # Make a new thread
    thread.daemon = True                        # Dies when main program dies
    thread.start()                              # Start the new thread

    while True:                                 # Main Loop
        
        time.sleep(1)                           # Wait 1 Second - Temporary Logic
        print("Main Loop")                      # Print "Main Loop" - Temporary Logic

                                                # Non-blocking check for new serial events
        while not event_queue.empty():          # Whenever the event queue is not empty...
            event = event_queue.get()           # Get the current state of the event queue from the serial thread
            print(f"Serial event: {event}")     # Print detection of connection or disconnection

        with serial_thread.devices_lock:                    # Lock while reading
            devices = dict(serial_thread.connected_devices) # Get list of all devices from the serial thread dictionary

main()  # Run Main Loop
