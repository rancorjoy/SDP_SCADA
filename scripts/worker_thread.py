# worker_thread
# This software thread asynchronously manages serial communication and SQL logging for one Arduino

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time

from . import print_log
from . import worker_thread_utils

# Function that defines a worker thread
def worker(port, cmd_queue):

    print_log.pL(f"Worker ({port})", "Event", "Worker thread initializing, opening port", "System", True, None)
    ser = worker_thread_utils.connect(port)  # establish serial connection once at thread start


    while True:
                                           
        try:                                # CHECK FOR COMMANDS 
            cmd = cmd_queue.get_nowait()    # Check if the command queue has received a message

            # Stop Command
            if cmd["command"] == "stop":    # If the stop command has been read...
                print_log.pL(f"Worker ({port})", "Event", "Worker thread stopping", "System", True, None)
                ser.close()                 # Close serial communication on the port
                return                      # Kill this worker thread
            

            # Pause Command
            if cmd["command"] == "pause":   # If the pause command has been read...
                print_log.pL(f"Worker ({port})", "Event", "Worker thread pausing, closing port", "System", True, None)
                ser.close()                 # Close serial communication on the port

            
            # Continue Command
            if cmd["command"] == "continue":            # If the comtinue command has been read...
                print_log.pL(f"Worker ({port})", "Event", "Worker thread continuing, reopening port", "System", True, None)
                ser = worker_thread_utils.connect(port) # Reopen port


            # Hold Enable Command
            elif cmd["command"].startswith("hold_en"):
                parts = cmd["command"].split()
                ser.write(f"hold_en {parts[1]} {parts[2]}\n".encode())

                if(parts[2] == "true"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold set on {parts[1]}", "System", True, None)

                if(parts[2] == "false"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold released on {parts[1]}", "System", True, None)


            # Hold (Value) Command
            elif cmd["command"].startswith("hold"):
                parts = cmd["command"].split()
                ser.write(f"hold {parts[1]} {parts[2]}\n".encode())

                print_log.pL(f"Worker ({port})", "Event", f"Hold on {parts[1]} set to {parts[2]}", "System", True, None)
        

        # No command
        except queue.Empty:                 # If no command has been received...
            pass                            # Move on until the next cycle, do not wait (non-blocking)

        # Collect Data Here
        #if ser.in_waiting:
        #    line = ser.readline().decode().strip()
        #    print(f"ARDUINO: {line}")
