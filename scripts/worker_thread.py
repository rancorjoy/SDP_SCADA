# worker_thread
# This software thread asynchronously manages serial communication and SQL logging for one Arduino

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time
import datetime
import sqlite3
import pathlib

from . import print_log
from . import dcs_dict_utils
from . import worker_thread_utils

# Function to get list of active points for logging
def get_active(current_dict, cont_name):
    active_points = dcs_dict_utils.list_points(
    current_dict[cont_name]["pin_config"],
    current_dict[cont_name]["software_points"],
    current_dict[cont_name]["timers"])
    return active_points

# Function that defines a worker thread
def worker(port, cmd_queue, sql_queue, current_dict, data_path):

    print_log.pL(f"Worker ({port})", "Event", "Worker thread initializing, opening port", "System", True, None)
    ser = worker_thread_utils.connect(port)  # establish serial connection once at thread start
    paused = False

    last_sample = 0 # Seconds since the thread has been enabled
    burst_buf = {}  # Buffer from the arduino being read

    active_points = {}  # The current list of active points
    valid_points = set()
    expected = 0

    # Ensure a connection to the sql database and make one if it got removed!
    db_conn = sqlite3.connect(str(pathlib.Path(data_path) / "data.db"), check_same_thread=False)
    db_conn.execute("PRAGMA journal_mode=WAL")
    db_conn.execute("PRAGMA synchronous=NORMAL")
    db_conn.execute("""
        CREATE TABLE IF NOT EXISTS point_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            port      TEXT,
            cont_name TEXT,
            point_name TEXT,
            val       TEXT
        )
    """)
    db_conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_point_log_lookup
        ON point_log (cont_name, timestamp)
    """)

    while True:

        for key in current_dict:
            if current_dict[key]["port"] == port:
                cont_name = key
        sample_time = current_dict[cont_name]["sample_time"]

        active_points = get_active(current_dict, cont_name)
        valid_points = set(active_points.keys())
        expected = len(valid_points)
                                           
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
                active_points = get_active(current_dict, cont_name)
                valid_points = set(active_points.keys())
                
                expected = len(valid_points)
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
                    now = time.time()

                    if now - last_sample < sample_time:
                        # Drain — keep serial buffer from backing up
                        if ser.in_waiting:
                            ser.read(ser.in_waiting)
                    else:
                        burst_buf = {}
                        ser.timeout = 0.3
                        while True:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if not line:
                                break
                            parts = line.split()
                            if len(parts) == 2:
                                key, val = parts[0], parts[1]
                                if key in valid_points:      # ← only accept known points
                                    if key in burst_buf:
                                        break                # second burst started
                                    burst_buf[key] = val
                        ser.timeout = None

                        if burst_buf:
                            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            db_conn.executemany(
                                "INSERT INTO point_log (port, cont_name, point_name, val, timestamp) VALUES (?, ?, ?, ?, ?)",
                                [(port, cont_name, name, val, ts) for name, val in burst_buf.items()]
                            )
                            while True:
                                try:
                                    db_conn.commit()
                                    break
                                except sqlite3.OperationalError:
                                    time.sleep(0.01)

                        last_sample = time.time()

                except serial.SerialException:
                    print_log.pL(f"Worker ({port})", "Event", "Worker thread stopping", "System", True, None)
                    ser.close()
                    return