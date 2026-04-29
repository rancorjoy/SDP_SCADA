# Import Needed Libraries
import os           # Operating System Management
import time         # Time Keeping and Sleep
import pathlib      # Object-Oriented File Path Management
import json         # JSON File Management
import shutil       # Shell Utilities (High Level File Operations)
import threading    # Multithreading for Commands Outside of Loop
import flask        # Lightweight web server
import requests     # For Command Line Interface Window
import serial                       # Serial Communications over USB<->USB
import serial.tools.list_ports      # Serial communication tools for port detection
import queue                        # Adds queues that can be pushed or popped to from a thread
from dataclasses import dataclass   # Allows current state to be passed as a struct to FLASK thread

# Import the scripts folder - scripts and utility methods
from scripts import data_path_utils
from scripts import dcs_dict_utils
from scripts import dcs_flash_utils
from scripts import flask_thread
from scripts import flash_thread
from scripts import serial_thread
from scripts import create_block_lib
from scripts import print_log
from scripts.current_state import CurrentState

def split_dcs_list(dcs_list):
    cont_list = {}
    prog_list = {}
    for key in dcs_list:
        if dcs_dict_utils.is_prog(dcs_list[key]):
            print("Test Condition")
            prog_list[key] = dcs_list[key]
        else:
            cont_list[key] = dcs_list[key]
    return cont_list, prog_list

def main():                                                         # Main Method - Program Entry Point
    
    print_log.pL("System", "Event", "Starting SCADA", "System", True, None)

                                                    # Initialize Data Path and Sub-Paths
    is_path = data_path_utils.init_data_path()      # Initialize Data Path
    path = data_path_utils.get_data_path()          # Get Current Data Path
    is_info = dcs_dict_utils.init_dcs_path(path)    # Initialize DCS Info Path
    is_sp = dcs_flash_utils.init_code_path(path)    # Initialize DCS Code Path
    is_bl = create_block_lib.initialize_block_lib() # Initialize Code Block Library in main path (persistent)
    blk_lib = create_block_lib.open_block_lib()     # Open a copy of the block library

    serial_queue = queue.Queue()                            # Create an event queue for the serial monitoring thread
    flash_queue = queue.Queue()                             # Create an event queue for flashing DCS controllers
    flash_lock = threading.Lock()                           # Create a lock for the flash thread
    
    current_dcs = {}                                        # Array for current dcs connections

    current_dict = {}                                                   # Dictionary for DCS details of each controller (current/unsaved versions)
    current_dict = dcs_dict_utils.init_current_dict(path)               # Get the (starting) current dictionary from previously learned devices
    current_dict_lock = threading.Lock()                                # Prevents errors from read/write collisions in the FLASK server
    dcs_dict_utils.load_progs(current_dict, current_dict_lock, path)    # Load all saved programs (empty controllers)

    devices = {}                                                        # Array for current devices (USB connections)
    previous_devices = {}                                               # Array for previous devices (USB connections)

    if is_path and is_bl:                                       # If the data path is initialized and code blocks are initialized (if not, nothing can/should run)
                                                                # Create a thread that runs serial_thread.serial_loop
                                                                # Pass the thread the event queue so results can be used in main thread
        monitor_thread = threading.Thread(target=serial_thread.serial_loop, args=(serial_queue,is_info))
        monitor_thread.daemon = True                            # Dies when main program dies
        monitor_thread.start()                                  # Start the new thread

        # Data structure being passed to the FLASK server with current state of system (pass by reference)
        thisState = CurrentState(current_dcs,current_dict, current_dict_lock, flash_queue, flash_lock, blk_lib) 

                                                                # Create a thread that runs flask_thread.flask_loop
        server_thread = threading.Thread(target=flask_thread.flask_loop, args=(thisState,)) 
        server_thread.daemon = True                             # Dies when main program dies
        server_thread.start()                                   # Start the new thread

                                                                # Create a thread that runs flash_thread.flash_loop
                                                                # Pass the thread the event flash so results can be used in main thread
        write_thread = threading.Thread(target=flash_thread.flash_loop, args=(flash_queue,flash_lock, path,is_sp))
        write_thread.daemon = True                              # Dies when main program dies
        write_thread.start()                                    # Start the new thread

        while True:                                             # Main Loop
        
                                                                        # Non-blocking check for new serial events
            while not serial_queue.empty():                             # Whenever the event queue is not empty...
                event = serial_queue.get()                              # Get the current state of the event queue from the serial thread
                                                                        # Print detection of connection or disconnection
                print_log.pL("Serial", "Event", f"Controller {event["event"]}, {event["port"]}", "System", True, None)
                                                                        # If a serial event has been detected... update device list:
            
                previous_devices = dict(devices)

                cont_list, prog_list = split_dcs_list(current_dict)

                with serial_thread.devices_lock:                    # Lock while reading
                    devices = dict(serial_thread.connected_devices) # Get list of all devices from the serial thread dictionary
                
                    # Newly connected devices
                    for device in devices.values():
                        if device not in previous_devices.values():
                            is_saved = dcs_dict_utils.init_dcs(path, device, current_dict, current_dict_lock)

                            if is_saved:
                                is_loaded = dcs_dict_utils.load_dcs(path, device["port"], current_dcs, current_dict, current_dict_lock)

                    # Disconnected devices
                    for device in previous_devices.values():
                        if device not in devices.values():
                            is_removed = dcs_dict_utils.unload_dcs(path, device["port"], current_dcs)
    
    else:                                               # If the data path is not initialized
        print_log.pL("System", "Error", "Data Path has failed to initialize", "System", True)
main()  # Run Main Loop
