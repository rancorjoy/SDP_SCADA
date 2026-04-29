# worker_thread_utils
# Contains functions for use in worker threads and in managing worker threads

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time

from . import print_log
from . import worker_thread
from . import dcs_dict_utils

# Call to add a worker thread at a port
def add_worker(port, worker_threads):
    cmd_queue = queue.Queue()
    t = threading.Thread(
        target = worker_thread.worker,
        args=(port, cmd_queue)
    )
    t.daemon = True
    t.start()
    worker_threads[port] = {"thread": t, "cmd_queue": cmd_queue}

# Call to kill a worker thread at a port
def remove_worker(port, worker_threads):
    if port in worker_threads:
        worker_threads[port]["cmd_queue"].put({"command": "stop"})
        worker_threads[port]["thread"].join()                       # Wait for thread loop to finish
        del worker_threads[port]                                    # Remove the thread from worker_threads

# Call to set hold enable on point (for worker thread) - called in FLASK
def hold_en_worker(port, worker_threads, point_name, value, current_dict, data_path):
    if port not in worker_threads:
        return False

    if point_name not in current_dict[dcs_dict_utils.port_to_name(data_path, port)]["software_points"]:
        return False

    if value == True:
        worker_threads[port]["cmd_queue"].put({"command": f"hold_en {point_name} true"})
        return True
    elif value == False:
        worker_threads[port]["cmd_queue"].put({"command": f"hold_en {point_name} false"})
        return True
    elif value.lower() == "true" or value.lower() == "false":
        if port in worker_threads:
            worker_threads[port]["cmd_queue"].put({"command": f"hold_en {point_name} {value.lower()}"})
            return True

# Calls the correct hold setting command - called in FLASK
def hold_worker(port, worker_threads, point_name, value, current_dict, data_path):

    if port not in worker_threads:
        return False

    if point_name not in current_dict[dcs_dict_utils.port_to_name(data_path, port)]["software_points"]:
        return False
    
    if current_dict[dcs_dict_utils.port_to_name(data_path, port)]["software_points"][point_name]["type"] == "bool":
        hold_bool_worker(port, worker_threads, point_name, value, current_dict, data_path)
        return True

    else:
        hold_num_worker(port, worker_threads, point_name, value, current_dict, data_path)
        return True

# Call to set hold value on point (for worker thread) (num)
def hold_num_worker(port, worker_threads, point_name, value, current_dict, data_path):
    if is_number(value):
        worker_threads[port]["cmd_queue"].put({"command": f"hold {point_name} {value}"})

# Call to set hold value on point (for worker thread) (bool)
def hold_bool_worker(port, worker_threads, point_name, value, current_dict, data_path):
    if value.lower() == "true" or value.lower() == "false":
        worker_threads[port]["cmd_queue"].put({"command": f"hold {point_name} {value.lower()}"})
    elif value == True:
        worker_threads[port]["cmd_queue"].put({"command": f"hold {point_name} true"})
    elif value == False:
        worker_threads[port]["cmd_queue"].put({"command": f"hold {point_name} false"})

# Helper function for hold value handling
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

