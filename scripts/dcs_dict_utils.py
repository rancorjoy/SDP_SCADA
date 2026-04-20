# dcs_dict_utils.py
# This file contains the methods needed to describe and load descriptions of dcs into main-thread memory

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

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
        "note": note
    }

# Returns Arduino UNO Default Pin Map
def uno_pin_map():
    pin_dict = {}

    for i in range(14):
      pin_dict[f"DP{i}"] = get_pin(f"DP{i}", False, False, False, None)
    
    for i in [3, 5, 6, 9, 10, 11]:
          pin_dict[f"DP{i}"]["pwn_capable"] = True                

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
def init_dcs(data_path, port):

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
    "software_points": {},
    "int_config": int_map
    }

    try:                                                                        # Try to write this JSON as a file
        file_path = data_path / "dcs_info" / f"{controller_name}.json"          # File path to dcs JSON files
        with open(file_path, 'w') as dcs_file:                                  # Open the file path and write
            json.dump(dcs_dict, dcs_file, indent=4)                             # JSON dump the dictionary for this controller
        return True                                                             # The DCS JSON was made

    except Exception as e:                                                      # If an exception is caught...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                            # The DCS JSON was not made (there was an error)

# Delete a dcs JSON from persistent data path for a given controller name
def delete_dcs(data_path, name, current_dcs):
    file_path = data_path / "dcs_info" / f"{name}.json"                   # The file path containing all controller JSONs
    try:                                                                  # Try to delete the file...
        unload_dcs(data_path, name_to_port(data_path, name),current_dcs); # Unload the old (defunct) data-structure
        file_path.unlink()                                                # Delete the file
        return True                                                       # The DCS JSON was deleted
    except FileNotFoundError:                                             # If the file is not found...
        print_log.pL("System", "Error", "No file found for controller: {name}.", "System", True, None)
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
def load_dcs(data_path, port, current_dcs):
    current_dict = create_dict(data_path, port)
    current_name = port_to_name(data_path, port)
    if current_dict != None:
        if current_name != None:
            current_dcs.update(current_dict)
            return True
    return False

# Remove a dcs JSON from current_dcs by port
def unload_dcs(data_path, port, current_dcs):
    current_name = port_to_name(data_path, port)
    try:
      return current_dcs.pop(current_name)
    except KeyError:
      print_log.pL("System", "Error", "The key '{current_name}' was not found in the dictionary.", "System", True, None)
      return False

# Rename a controller
def rename_dcs(data_path, old_name, new_name, current_dcs): 
    file_path = data_path / "dcs_info" / f"{old_name}.json"                   # Get the file path for the current controller
    new_path  = data_path / "dcs_info" / f"{new_name}.json"                   # Get the proposed file path for the current controller
    if not file_path.is_file():                                               # If the OLD file doesn't exist...
        print_log.pL("System", "Error", "The dcs info file '{old_name}.json' was not found.", "System", True, None)  
        return False                                                          # The controller's name was not changed
    if new_path.is_file():                                                    # If the NEW name is already taken...
        print_log.pL("System", "Error", "A controller named '{new_name}' already exists.", "System", True, None) 
        return False                                                          # The controller's name was not changed
    try:                                                                      # If those two conditions fail (good news)... try:
        port = name_to_port(data_path, old_name)                              # Get the port name from the DCS
        if port is None:                                                      # If port not found...
          print_log.pL("System", "Error", "Could not find port for '{old_name}'.", "System", True, None)            
          return False                                                        # The controller's name was not changed
        unload_dcs(data_path, port, current_dcs);                             # Unload the old (defunct) data-structure

        file_path.rename(new_path)                                            # Rename the old file to the new files
        with open(new_path, 'r') as f:                                        # Open the renamed file as f (read only)
          dcs = json.load(f)                                                  # Load the json from f as dcs
        dcs["name"] = new_name                                                # Update the name inside of dcs
        with open(new_path, 'w') as f:                                        # With the new file open (write) as f
          json.dump(dcs, f, indent=4)                                         # Write dcs to f, this ensures the file updates
        load_dcs(data_path, port, current_dcs);                               # Load in the new data-structure
        return True                                                           # The controller's name WAS changed
    
    except Exception as e:                                                    # If an exception is thrown...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                          # The controller's name was not changed