# worker_thread
# This software thread asynchronously manages serial communication and SQL logging for one Arduino

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time
import datetime

from . import print_log
from . import worker_thread_utils

# Function that defines a worker thread
def worker(port, cmd_queue, sql_queue, cont_name, current_dict):

    print_log.pL(f"Worker ({port})", "Event", "Worker thread initializing, opening port", "System", True, None)
    ser = worker_thread_utils.connect(port)  # establish serial connection once at thread start
    paused = False

    last_sample = 0 # Seconds since the thread has been enabled

    while True:

        sample_time = current_dict[cont_name]["sample_time"]
                                           
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
                paused = True
                if "ready" in cmd:
                    cmd["ready"].set()  # signal that port is closed

            
            # Continue Command
            if cmd["command"] == "continue":            # If the comtinue command has been read...
                print_log.pL(f"Worker ({port})", "Event", "Worker thread continuing, reopening port", "System", True, None)
                ser = worker_thread_utils.connect(port) # Reopen port
                ser.reset_input_buffer()                # clear reset garbage after reconnect only
                paused = False

                ser.flush()
                time.sleep(0.15)

            # Hold Enable Command
            elif cmd["command"].startswith("hold_en"):
                parts = cmd["command"].split()
                ser.write(f"hold_en {parts[1]} {parts[2]}\n".encode())

                if(parts[2] == "true"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold set on {parts[1]}", "System", True, None)

                if(parts[2] == "false"):
                    print_log.pL(f"Worker ({port})", "Event", f"Hold released on {parts[1]}", "System", True, None)

                ser.flush()
                time.sleep(0.15)


            # Hold (Value) Command
            elif cmd["command"].startswith("hold"):
                parts = cmd["command"].split()
                ser.write(f"hold {parts[1]} {parts[2]}\n".encode())

                print_log.pL(f"Worker ({port})", "Event", f"Hold on {parts[1]} set to {parts[2]}", "System", True, None)
        

        # No command -> collect data!
        except queue.Empty:
            if not paused:
                try:
                    ser.write(b"poll\n")
                    ser.flush()
                    if ser.in_waiting:
                        line = ser.readline().decode().strip()
                        #print(f"ARDUINO: [{line}]")  # temporary debug
                        parts = line.split()
                        if len(parts) == 2:
                            now = time.time()
                            if now - last_sample >= sample_time:  # only log at sample_time rate
                                sql_queue.put({
                                    "port": port, 
                                    "cont_name" : cont_name, 
                                    "point_name": parts[0], 
                                    "val": parts[1]
                                    })
                                last_sample = now
                            # if not time yet, line is just discarded -> buffer still drained
                except serial.SerialException:
                    print_log.pL(f"Worker ({port})", "Event", "Worker thread stopping", "System", True, None)
                    ser.close()
                    return