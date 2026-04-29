# worker_thread
# This software thread asynchronously manages serial communication and SQL logging for one Arduino

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time

from . import print_log

# Function that defines a worker thread
def worker(port, cmd_queue):

    print_log.pL(f"Worker ({port})", "Event", "Worker thread initializing", "System", True, None)


    while True:
                                           
        try:                                # CHECK FOR COMMANDS 
            cmd = cmd_queue.get_nowait()    # Check if the command queue has received a message

            if cmd["command"] == "stop":    # If the stop command has been read...
                print_log.pL(f"Worker ({port})", "Event", "Worker thread stopping", "System", True, None)
                return                      # Kill this worker thread
            
            elif cmd["command"].startswith("hold_en"):
                parts = cmd["command"].split()

                if(parts[2] == "true"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold set on {parts[1]}", "System", True, None)

                if(parts[2] == "false"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold released on {parts[1]}", "System", True, None)

            elif cmd["command"].startswith("hold"):
                parts = cmd["command"].split()

                print_log.pL(f"Worker ({port})", "Event", f"Hold on {parts[1]} set to {parts[2]}", "System", True, None)
        
        except queue.Empty:                 # If no command has been received...
            pass                            # Move on until the next cycle, do not wait (non-blocking)

        # Collect Data Here
