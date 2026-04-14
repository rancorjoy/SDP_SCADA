# serial_thread
# This software thread asynchronously refreshes the list of active serial connections to ensure all DCS are detected

# Import Needed Libraries
import queue                                    # Adds queues that can be pushed or popped to from a thread
import time                                     # Time Keeping and Sleep
import threading                                # Multithreading for Commands Outside of Loop
import serial                                   # Serial Communications over USB<->USB
import serial.tools.list_ports                  # Serial communication tools for port detection

from . import data_path_utils                   # Import the data_path_utils script (current) folder
from . import scan_serial                       # Import the scan_serial script (current) folder

connected_devices = {}                          # Shared dictionary - accessed from outside of this thread
devices_lock = threading.Lock()                 # Prevents simultaneous read/write corruption

def get_port_details(target_port, current_ports):       # Method gets all information from a connected serial port
    for port in current_ports:                          # Check all current ports for the target port...
        if port.device == target_port:                  # If the indexed port is the target port...
            return {                                    # Return a JSON encoded port information packet
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer,
                "serial_number": port.serial_number,
                "vid": port.vid,
                "pid": port.pid
            }
    return None                                         # If the target port was not found, return nothing (fail silently)

def serial_loop(event_queue, is_init):                                              # Method is ran in entry point - returns "queue" of serial events
    prev_ports = set()                                                              # Create an empty set of previous ports
    while True:                                                                     # Continously while the main thread runs...
        
        if is_init:
            port_objects = serial.tools.list_ports.comports()                           # Call comports() to find all current port connections
            current_ports = set(p.device for p in port_objects)                         # Set of device name strings for comparison
        
            for port in current_ports - prev_ports:                                     # For all ports found this cycle...
                details = get_port_details(port, port_objects)                          # Store full port information is 'details'
                with devices_lock:                                                      # Prevents simultaneous read/write corruption
                    connected_devices[port] = details                                   # Set the connected_devices[port] entry to 'details'
                event_queue.put({"event": "connected", "port": port})                   # Send new connection to queue
        
            for port in prev_ports - current_ports:                                     # For all ports NOT found this cycle...
                with devices_lock:                                                      # Prevents simultaneous read/write corruption
                    connected_devices.pop(port, None)                                   # Remove this device from connected_devices
                event_queue.put({"event": "disconnected", "port": port})                # Send new disconnection to queue
        
        prev_ports = current_ports                                                  # Update previous ports
        time.sleep(1)                                                               # Wait 1 second before checking ports again