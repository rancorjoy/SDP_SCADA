# dcs_dict_utils.py
# This file contains the methods needed to describe and load descriptions of dcs into main-thread memory

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

from . import dcs_script_utils
from . import print_log

# Initialize dcs folder inside persistent data path
def init_dcs_path(data_path):

    data_path = pathlib.Path(data_path)                     # Ensure data path is a path (works for path and string inputs)
    dcs_path = data_path / pathlib.Path("dcs_info")         # Assign dcs_path to data_path/dcs_info (name of folder)

    try:                                                    # Attempt to make folder if it does not exist
        dcs_path.mkdir(parents=True, exist_ok=True)         # parents=True creates any missing parent directories
        return True                                         # The folder was initialized
    except FileExistsError:                                 # If the folder exists and is blocking verification
        return True                                         # The folder was initialized before (just in case)
    except Exception as e:                                  # Handle other potential errors like permission issues
        print_log.pL("System", "Error", "An unexpected error occurred", "System", True, {e})
        return False                                        # The folder was not initialized

# Get the plugged in Arduino Model
def get_dcs_type(port):
    vid = port.get("vid")                                 # Try identifying by VID/PID (Linux Friendly)
    pid = port.get("pid")                                 # Note: These are often integers when coming from pyserial

    if vid == 0x2341 and pid in [0x0010, 0x0042]:         # Arduino Mega 2560 IDs
        return "MEGA"
    
    if vid == 0x2341 and pid in [0x0043, 0x0001]:         # Arduino Uno IDs
        return "UNO"

    description = (port.get("description") or "").upper() # Fallback to Description (Windows legacy)
    if "MEGA" in description:                             # Arduino Mega 2560 IDs
        return "MEGA"
    elif "UNO" in description:                            # Arduino Uno IDs
        return "UNO"

    return None

# Returns a Pin Map for specified data
def get_pin(pin_name, is_pwm, is_analog, is_int, note):
    return {
        "name": pin_name,
        "direction": "INPUT",                   # INPUT, INPUT_PULLUP, OUTPUT
        "enabled": False,
        "pwm_capable": is_pwm,
        "analog_capable": is_analog,
        "interrupt_capable": is_int,
        "analog_set" : False,                   # Is the pin currently analog?
        "pwm_set" : None,                       # Give the PWM value a software point as its value
        "int_set" : False,                      # Is the interrupt being used?
        "note": note
    }

# Returns a Data Map for a default software point
def get_software_point():   # The defualt software point is always the same
    return {
        "type": "int",      # int, float or bool
        "default" : 1,      # default value
        "hold" : False,     # is the default value being overriden (serial)?
        "hold_val" : 1,     # what is the hold value if being held?
        "min_en" : False,   # is the value held at or above a value? (not available for bool)
        "max_en" : False,   # is the value held at or below a value? (not available for bool)
        "min" : 0,          # minimum value (not available for bool)
        "max" : 1,          # maximum value (not available for bool)
        "hardware" : False  # is this pin tied to hardware? (cannot be removed)
    }

# Returns a list of software points that correlate with each pin
def get_hardware_points(pin_map):

    point_map = {}                  # Point map that will be returned

    for key, val in pin_map.items():
        new_point = get_software_point()
        new_point["type"] = "bool"
        new_point["hardware"] = True

        point_map[key] = new_point
    
    return point_map                # This map is populated with all needed hardware points

# Returns Arduino UNO Default Pin Map
def uno_pin_map():
    pin_dict = {}

    for i in range(14):
      pin_dict[f"DP{i}"] = get_pin(f"DP{i}", False, False, False, None)
    
    for i in [3, 5, 6, 9, 10, 11]:
          pin_dict[f"DP{i}"]["pwm_capable"] = True                

    for i in [2, 3]:
        pin_dict[f"DP{i}"]["interrupt_capable"] = True

    for i in range(6):
        pin_dict[f"AP{i}"] = get_pin(f"AP{i}", False, True, False, None)
          
    pin_dict["DP0"]["note"] = "RX - reserved for serial"
    pin_dict["DP1"]["note"] = "TX - reserved for serial"
    pin_dict["DP13"]["note"] = "built-in LED"
    pin_dict["AP4"]["note"] = "SDA - reserved if using I2C"
    pin_dict["AP5"]["note"] = "SCL - reserved if using I2C"

    return pin_dict

# Returns Arduino UNO Interrupt Map
def uno_int_map():
    int_dict = {
        "2": {
            "ISR_name": "ISR2",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "3": {
            "ISR_name": "ISR3",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        }
    }
    return int_dict

# Returns Arduino MEGA Default Pin Map
def mega_pin_map():
    pin_dict = {}

    for i in range(54):
      pin_dict[f"DP{i}"] = get_pin(f"DP{i}", False, False, False, None)
    
    for i in range(2, 14):
            pin_dict[f"DP{i}"]["pwm_capable"] = True 

    for i in range(44, 47):
            pin_dict[f"DP{i}"]["pwm_capable"] = True 

    for i in [2, 3, 18, 19, 20, 21]:
        pin_dict[f"DP{i}"]["interrupt_capable"] = True

    for i in range(16):
        pin_dict[f"AP{i}"] = get_pin(f"AP{i}", False, True, False, None)
          
    pin_dict["DP0"]["note"] = "RX0 - reserved for serial"
    pin_dict["DP1"]["note"] = "TX0 - reserved for serial"
    pin_dict["DP13"]["note"] = "built-in LED"
    pin_dict["DP14"]["note"] = "TX3 - reserved for serial"
    pin_dict["DP15"]["note"] = "RX3 - reserved for serial"
    pin_dict["DP16"]["note"] = "TX2 - reserved for serial"
    pin_dict["DP17"]["note"] = "RX2 - reserved for serial"
    pin_dict["DP18"]["note"] = "TX1 - reserved for serial"
    pin_dict["DP19"]["note"] = "RX1 - reserved for serial"
    pin_dict["DP20"]["note"] = "SDA - reserved for I2C"
    pin_dict["DP21"]["note"] = "SCL - reserved for I2C"

    return pin_dict

# Returns Arduino MEGA Interrupt Map
def mega_int_map():
    int_dict = {
        "2": {
            "ISR_name": "ISR2",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "3": {
            "ISR_name": "ISR3",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "18": {
            "ISR_name": "ISR18",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "19": {
            "ISR_name": "ISR19",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "20": {
            "ISR_name": "ISR20",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        },
        "21": {
            "ISR_name": "ISR21",
            "Mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "High": False,          # HIGH is not available on this board
            "Enabled": False
        }
    }
    return int_dict

# Check if there exists a matching dcs JSON for given controller
def check_saved(data_path, port):
    dcs_dir = data_path / "dcs_info"                            # The file path containing all controller JSONs
    for file in dcs_dir.glob("*.json"):                         # Check every JSON in the folder...
        with open(file, 'r') as f:                              # Open each file in read mode...
          dcs = json.load(f)                                    # Load each file in read mode...
        if dcs.get("serial_number") == port["serial_number"]:   # If serial number matches...
          
          dcs["hwid"] = port["hwid"]                            # Ensure any hwid changes are saved
          dcs["port"] = port["port"]                            # Ensure any port changes are saved

          if file.stem != dcs.get("name"):                      # When opening an existing file, ensure the names match!
            dcs["name"] = file.stem                             # Always ensure the nickname matches the file name

          with open(file, 'w') as f:                            # Write changes back to disk
            json.dump(dcs, f, indent=4)                         # Write as json dump (consistent with original definition)

          return True                                           # This port is already saved as a JSON
    return False                                                # If not, this port is not saved as a JSON yet

# Create a new dcs JSON for a new controller in persistent data path if there is not one, initialize if there is one
def init_dcs(data_path, port, current_dict, current_dict_lock):

                                                # Check for existing dcs JSON for this device's serial number
    if check_saved(data_path, port):            # If the current port is already saved
        return True                             # Return True (there is a valid JSON file for this port)

    dcs_type = get_dcs_type(port)               # Get the board type for the given port
    if dcs_type == "UNO":                       # If the board is an UNO, assign the pin and interrupt maps for UNO
        pin_map = uno_pin_map()
        int_map = uno_int_map()
        fqbn = "arduino:avr:uno"
    elif dcs_type == "MEGA":                    # If the board is an MEGA, assign the pin and interrupt maps for MEGA
        pin_map = mega_pin_map()
        int_map = mega_int_map()
        fqbn = "arduino:avr:mega"
    else:                                       # If the port is not an arduino board...
        return False                            # The DCS JSON was not made (there is no target)
    
                                                                # Find the next available controller index
    dcs_dir = data_path / "dcs_info"                            # The file path containing all controller JSONs
    existing = list(dcs_dir.glob("unnamed_controller_*.json"))  # Find all unnamed controllers
    n = len(existing)                                           # Next gaurenteed unnamed controller index
    controller_name = f"unnamed_controller_{n}"                 # Use the controller index to generate the file/nick-name

                                                # Create a JSON Dictionary that contains the default controller configuration
    dcs_dict = {                                # Default Controller Setings:
    "description": port["description"],
    "hwid": port["hwid"],
    "manufacturer": port["manufacturer"],
    "serial_number": port["serial_number"],
    "port": port["port"],      
    "vid": port["vid"],
    "pid": port["pid"],
    "name": controller_name,
    "fqbn": fqbn,
    "pin_config": pin_map,
    "software_points": get_hardware_points(pin_map),
    "int_config": int_map
    }

    try:                                                                        # Try to write this JSON as a file
        file_path = data_path / "dcs_info" / f"{controller_name}.json"          # File path to dcs JSON files
        with open(file_path, 'w') as dcs_file:                                  # Open the file path and write
            json.dump(dcs_dict, dcs_file, indent=4)                             # JSON dump the dictionary for this controller
        
        dcs_script_utils.create_Script(data_path, controller_name)
        with current_dict_lock:
            add_current_dict(current_dict, data_path, controller_name)

        return True                                                             # The DCS JSON was made and the ino

    except Exception as e:                                                      # If an exception is caught...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                            # The DCS JSON was not made (there was an error)

# Delete a dcs JSON from persistent data path for a given controller name
def delete_dcs(data_path, name, current_dcs, current_dict, current_dict_lock):
    file_path = data_path / "dcs_info" / f"{name}.json"                   # The file path containing all controller JSONs
    try:                                                                  # Try to delete the file...
        unload_dcs(data_path, name_to_port(data_path, name),current_dcs); # Unload the old (defunct) data-structure
        file_path.unlink()                                                # Delete the file

        script_path = data_path / pathlib.Path("dcs_scripts")
        dcs_script_utils.remove_Script(script_path, name)

        with current_dict_lock:
            remove_current_dict(current_dict, data_path, name)

        return True                                                       # The DCS JSON was deleted
    except FileNotFoundError:                                             # If the file is not found...
        print_log.pL("System", "Error", f"No file found for controller: {name}.", "System", True, None)
        return False                                                      # Nothing to delete
    except Exception as e:                                                # If there is another exception...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e}) 
        return False                                                      # The DCS JSON was not deleted
      
# Return name of existing JSON file from port
def port_to_name(data_path, port):            
    dcs_dir = data_path / "dcs_info"                # The file path for all named controllers
    for file in dcs_dir.glob("*.json"):             # For json file in the file path...
        with open(file, 'r') as f:                  # Open the file (read only) as f...
            dcs = json.load(f)                      # Load dcs from f (json)
        if dcs.get("port") == port:                 # If this dcs has the given port...
            return dcs.get("name")                  # Return the name of the dcs
    return None                                     # If none exist, return none

# Return port from name of existing JSON file
def name_to_port(data_path, name):
    file_path = data_path / "dcs_info" / f"{name}.json"         # The file path for the named controller
    if not file_path.is_file():                                 # If the file doesn't exist...
        return None                                             # Return None
    with open(file_path, 'r') as f:                             # Open the file in read mode...
        dcs = json.load(f)                                      # Load the JSON...
    return dcs.get("port")                                      # Return the port field, or None if missing

# Create dcs dict item for current_dcs from dcs JSON
def create_dict(data_path, port):                                                  
    name = port_to_name(data_path, port)                    # Get the name of the controller from the port
    if name is not None:                                    # If the name exists (as a string)...
        file_path = data_path / "dcs_info" / f"{name}.json" # Get the data-path of the relevant info json file
        with open(file_path, 'r') as f:                     # Open the json file (read only) as f
            dcs = json.load(f)                              # Load the json data from this file
        current_dict = {                                    # Create a dictionary element for the dcs element
            name: {                                         # The controller is accessed by name
                "serial_number": dcs["serial_number"],      # Add the serial number
                "port": port                                # Add the port
            }
        }
        return current_dict
    return None

# Load a dcs JSON into current_dcs by port
def load_dcs(data_path, port, current_dcs, current_dict, current_dict_lock):
    current_dict = create_dict(data_path, port)
    current_name = port_to_name(data_path, port)
    if current_dict != None:
        if current_name != None:
            current_dcs.update(current_dict)

            script_path = data_path / "dcs_scripts" / current_name
            if not script_path.exists():
                dcs_script_utils.create_Script(data_path, current_name)

            with current_dict_lock:
                add_current_dict(current_dict, data_path, current_name)

            return True
    return False

# Remove a dcs JSON from current_dcs by port
def unload_dcs(data_path, port, current_dcs):
    current_name = port_to_name(data_path, port)
    try:
      return current_dcs.pop(current_name)
    except KeyError:
      print_log.pL("System", "Error", f"The key '{current_name}' was not found in the dictionary.", "System", True, None)
      return False

# Rename a controller
def rename_dcs(data_path, old_name, new_name, current_dcs, current_dict, current_dict_lock): 
    file_path = data_path / "dcs_info" / f"{old_name}.json"                   # Get the file path for the current controller
    new_path  = data_path / "dcs_info" / f"{new_name}.json"                   # Get the proposed file path for the current controller
    if not file_path.is_file():                                               # If the OLD file doesn't exist...
        print_log.pL("System", "Error", f"The dcs info file '{old_name}.json' was not found.", "System", True, None)  
        return False                                                          # The controller's name was not changed
    if new_path.is_file():                                                    # If the NEW name is already taken...
        print_log.pL("System", "Error", f"A controller named '{new_name}' already exists.", "System", True, None) 
        return False                                                          # The controller's name was not changed
    try:                                                                      # If those two conditions fail (good news)... try:
        port = name_to_port(data_path, old_name)                              # Get the port name from the DCS
        if port is None:                                                      # If port not found...
          print_log.pL("System", "Error", f"Could not find port for '{old_name}'.", "System", True, None)            
          return False                                                        # The controller's name was not changed
        
        was_loaded = False                                                    # Was the controller loaded?
        if old_name in current_dcs:                                           # If the controller was loaded
            unload_dcs(data_path, port, current_dcs);                         # Unload the old (defunct) data-structure

        file_path.rename(new_path)                                            # Rename the old file to the new files
        with open(new_path, 'r') as f:                                        # Open the renamed file as f (read only)
          dcs = json.load(f)                                                  # Load the json from f as dcs
        dcs["name"] = new_name                                                # Update the name inside of dcs
        with open(new_path, 'w') as f:                                        # With the new file open (write) as f
          json.dump(dcs, f, indent=4)                                         # Write dcs to f, this ensures the file updates

        if was_loaded:                                                        # If the controller was loaded when the name was changed...
            load_dcs(data_path, port, current_dcs);                           # Load in the new data-structure

        dcs_script_utils.create_Script(data_path, old_name)                
        dcs_script_utils.rename_Script(data_path, old_name, new_name)

        with current_dict_lock:
            current_dict[new_name] = current_dict[old_name]                   # Copy data to new key
            del current_dict[old_name]                                        # Remove old key

        return True                                                           # The controller's name WAS changed
    
    except Exception as e:                                                    # If an exception is thrown...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                          # The controller's name was not changed
    
def get_pin_from_name(pin_dict, name):
    for key, val in pin_dict.items():
        if val["name"] == name:
            return key
        
    return None


# === Functions to managed loaded and saved JSON files

# Returns the current dictionary that contains all JSON files in the info folder
def init_current_dict(data_path):
    data_path = pathlib.Path(data_path)
    dcs_path = data_path / pathlib.Path("dcs_info")         # Assign dcs_path to data_path/dcs_info (name of folder)

    
    if not dcs_path.exists():
        print_log.pL("System", "Error", "Data Path Directory not found.", "System", True, None)
    if not dcs_path.is_dir():
        print_log.pL("System", "Error", "Data Path Directory not a directory.", "System", True, None)
    
    curr_dict = {}
    for json_file in dcs_path.glob("*.json"):
        with json_file.open("r", encoding="utf-8") as f:
            curr_dict[json_file.stem] = json.load(f)
    
    return curr_dict

# Adds a json to the current dictionary
def add_current_dict(curr_dict, data_path, name):
    if name in curr_dict:
        return curr_dict  # Already loaded, do nothing
    
    json_file = pathlib.Path(data_path) / "dcs_info" / f"{name}.json"
    
    if not json_file.exists():
        print_log.pL("System", "Error", f"JSON file '{name}' not found.", "System", True, None)
        return curr_dict
    
    with json_file.open("r", encoding="utf-8") as f:
        curr_dict[name] = json.load(f)
    
    return curr_dict

# Removes a json from the current dictionary
def remove_current_dict(curr_dict, filename):
    if filename not in curr_dict:
        print_log.pL("System", "Error", f"JSON file '{filename}' not in dictionary.", "System", True, None)
        return curr_dict
    
    del curr_dict[filename]
    return curr_dict

# Saves a json from the current directory back into the file (save settings)
def save_current_dict(curr_dict, data_path, name):
    if name not in curr_dict:
        print_log.pL("System", "Error", f"JSON file '{name}' not in dictionary.", "System", True, None)
        return False
    
    json_file = pathlib.Path(data_path) / "dcs_info" / f"{name}.json"
    
    with json_file.open("w", encoding="utf-8") as f:
        json.dump(curr_dict[name], f, indent=4)
        return True

# Flask call to save current dict with locking
def save_locked_dict(curr_dict, current_dict_lock, data_path, name):
    with current_dict_lock:
        return save_current_dict(curr_dict, data_path, name)

# Resets a json from the current directory (opposite of saving)
def reset_current_dict(curr_dict, data_path, name):
    json_file = pathlib.Path(data_path) / "dcs_info" / f"{name}.json"
    
    if not json_file.exists():
        print_log.pL("System", "Error", f"JSON file '{name}' not found.", "System", True, None)
        return False
    
    with json_file.open("r", encoding="utf-8") as f:
        curr_dict[name] = json.load(f)
    
    return True

# Flask call to reset current dict with locking
def reset_locked_dict(curr_dict, current_dict_lock, data_path, name):
    with current_dict_lock:
        return reset_current_dict(curr_dict, data_path, name)








# === Functions to change pin settings ===

def change_pin_enable(pin_dict, pin, value):
    if not isinstance(value, bool):
        return False
    if pin in pin_dict:
        pin_dict[pin]["enabled"] = value
        return True
    return False

def change_pin_name(pin_dict, pin, name):
    for key, val in pin_dict.items():
        if key != pin and val["name"] == name:
            return False
    pin_dict[pin]["name"] = name
    return True

def change_pin_type(pin_dict, point_dict, pin, analog):
    if pin_dict[pin]["analog_capable"]:
        if analog:
            change_pin_dir(pin_dict, pin, "INPUT")
            change_point_type(pin_dict, point_dict, pin, "int")
        pin_dict[pin]["analog_set"] = analog
        return True
    return False

def change_pin_dir(pin_dict, pin, dir):
    if pin_dict[pin]["analog_set"]:
        return False
    if pin_dict[pin]["int_set"]:
        return False
    if dir in ["INPUT", "INPUT_PULLUP", "OUTPUT"]:
        pin_dict[pin]["direction"] = dir
        return True
    return False

def change_pin_pwm(pin_dict, pin, point_dict, point):
    if point == None or point == "None":                # If PWM is being disabled (point is None)
        pin_dict[pin]["pwm_set"] = None                 # Remove the PWM point and don't replace it
        return True
    if not pin_dict[pin]["pwm_capable"]:
        return False
    if point is not None:
        if point not in point_dict:
            return False
        change_pin_dir(pin_dict, pin, "OUTPUT")
        pin_dict[pin]["pwm_set"] = {point: point_dict[point]}
    else:
        pin_dict[pin]["pwm_set"] = None
    return True

def change_pin_int(pin_dict, pin, int):
    if pin_dict[pin]["interrupt_capable"]:
        pin_dict[pin]["int_set"] = int
        if int:
            change_pin_dir(pin_dict, pin, "INPUT")
        return True
    return False



# === Functions to change point settings ===

def change_point_name(pin_dict, point_dict, old_name, new_name): 
    if point_dict[old_name]["hardware"]:                            # Do not change hardware pin names!
        return False
    if old_name in point_dict:
        if new_name in point_dict:
            return False
        point_dict[new_name] = point_dict[old_name]
        del point_dict[old_name]
        for key, val in pin_dict.items():
            if val["pwm_set"] is not None and old_name in val["pwm_set"]:
                val["pwm_set"] = {new_name: point_dict[new_name]}
        return True
    return False

def add_point(point_dict, name):
    if name in point_dict:  # dict membership checks keys directly
        return False
    point_dict[name] = get_software_point()
    return True

def rem_point(pin_dict, point_dict, name):
    if name not in point_dict:
        return False
    if point_dict[name]["hardware"] == False: #Stops key deletion if key is hardware, disabled pins will not print to SQL but will have points!
        del point_dict[name]
        for key, val in pin_dict.items():
            if val["pwm_set"] is not None and name in val["pwm_set"]:
                val["pwm_set"] = None
        return True
    return False

def change_point_type(pin_dict, point_dict, point, type):
    if point in point_dict:
        if type in ["int", "float", "bool"]:
            point_dict[point]["type"] = type
            if type == "bool":
                if pin_dict[point]["analog_set"]:
                    return False
                point_dict[point]["min_en"] = False
                point_dict[point]["max_en"] = False
                point_dict[point]["max"] = 1
                point_dict[point]["min"] = 0
                if point_dict[point]["hold_val"] > 0:
                    point_dict[point]["hold_val"] = 1
                if point_dict[point]["default"] > 0:
                    point_dict[point]["default"] = 1
            if type == "int":
                point_dict[point]["hold_val"] = int(point_dict[point]["hold_val"])
                point_dict[point]["min"] = int(point_dict[point]["min"])
                point_dict[point]["max"] = int(point_dict[point]["max"])
            if type == "float":
                if pin_dict[point]["analog_set"]:
                    return False
                point_dict[point]["hold_val"] = float(point_dict[point]["hold_val"])
                point_dict[point]["min"] = float(point_dict[point]["min"])
                point_dict[point]["max"] = float(point_dict[point]["max"])
            return True
    return False

def change_point_def(point_dict, point, value):
    if point not in point_dict:
        return False
    
    point_type = point_dict[point]["type"]
    
    if point_type == "bool":
        if not isinstance(value, bool) and value not in [0, 1]:
            return False
    elif point_type == "int":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        value = int(value)  # coerce float to int if needed
    elif point_type == "float":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        value = float(value)  # coerce int to float if needed
    
    # Check min/max bounds if enabled
    if point_dict[point].get("min_en") and value < point_dict[point]["min"]:
        return False
    if point_dict[point].get("max_en") and value > point_dict[point]["max"]:
        return False
    
    point_dict[point]["default"] = value
    return True

def change_point_hold_val(point_dict, point, value):
    if point not in point_dict:
        return False
    
    point_type = point_dict[point]["type"]
    
    if point_type == "bool":
        if not isinstance(value, bool) and value not in [0, 1]:
            return False
    elif point_type == "int":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        value = int(value)  # coerce float to int if needed
    elif point_type == "float":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        value = float(value)  # coerce int to float if needed
    
    # Check min/max bounds if enabled
    if point_dict[point].get("min_en") and value < point_dict[point]["min"]:
        return False
    if point_dict[point].get("max_en") and value > point_dict[point]["max"]:
        return False
    
    point_dict[point]["hold_val"] = value
    if point_dict[point]["type"] == "int":
        point_dict[point]["hold_val"] = int(value)
    return True

def change_point_hold_en(point_dict, point, value):
    if not isinstance(value, bool):
        return False
    if point in point_dict:
        point_dict[point]["hold"] = value
        return True
    return False

def change_point_min_en(point_dict, point, value):
    if not isinstance(value, bool):
        return False
    if point in point_dict:
        if point_dict[point]["type"] == "bool":
            return False
        point_dict[point]["min_en"] = value
        return True
    return False

def change_point_max_en(point_dict, point, value):
    if not isinstance(value, bool):
        return False
    if point in point_dict:
        if point_dict[point]["type"] == "bool":
            return False
        point_dict[point]["max_en"] = value
        return True
    return False

def change_point_min(point_dict, point, value):
    if point not in point_dict:
        return False
    if point_dict[point]["type"] == "bool":
        return False
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    if point_dict[point]["max_en"] and value > point_dict[point]["max"]:
        return False
    point_dict[point]["min"] = value
    if point_dict[point]["type"] == "int":
        point_dict[point]["min"] = int(value)
    return True

def change_point_max(point_dict, point, value):
    if point not in point_dict:
        return False
    if point_dict[point]["type"] == "bool":
        return False
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    if point_dict[point]["min_en"] and value < point_dict[point]["min"]:
        return False
    point_dict[point]["max"] = value
    if point_dict[point]["type"] == "int":
        point_dict[point]["max"] = int(value)
    return True

def list_pins(pin_dict, active): # Returns point_dict, only enabled pins if active is true
    if active:
        active_dict = {}
        for key in pin_dict:
            if pin_dict[key]["enabled"]:
                active_dict[key] = pin_dict[key]
        return active_dict
    else:
        return pin_dict
    
def list_points(pin_dict, point_dict): # Returns all software points and active hardware points
    active_dict = {}
    for key in point_dict:
        if point_dict[key]["hardware"] == False:
            active_dict[key] = point_dict[key]
        elif pin_dict[key]["enabled"]:
            active_dict[key] = point_dict[key]
    return active_dict


