# dcs_dict_utils.py
# DESCRIBE

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

# Initialize dcs folder inside persistent data path
def init_dcs_path(data_path):

    data_path = pathlib.Path(data_path)                     # Ensure data path is a path (works for path and string inputs)
    dcs_path = data_path / pathlib.Path("dcs_info")         # Assign dcs_path to data_path/dcs_info (name of folder)

    try:                                                    # Attempt to make folder if it does not exist
        dcs_path.mkdir(parents=True, exist_ok=True)         # parents=True creates any missing parent directories
        print(f"DCS Datapath '{dcs_path}' Initialized")     # Print verification to console
        return True                                         # The folder was initialized
    except FileExistsError:                                 # If the folder exists and is blocking verification
        print(f"Folder '{dcs_path}' already exists.")       # This should not be possible as exist_ok=True...
        return True                                         # The folder was initialized before (just in case)
    except Exception as e:                                  # Handle other potential errors like permission issues
        print(f"An error occurred: {e}")                    # Print error information
        return False                                        # The folder was not initialized

# Get the plugged in Arduino Model
def get_dcs_type(port):
    description = (port["description"] or "").upper()       # The description should contain either UNO or MEGA for the supported boards
    
    if "MEGA" in description:                               # If MEGA is in the description...
        return "MEGA"                                       # Return "MEGA"
    elif "UNO" in description:                              # If UNO is in the description...
        return "UNO"                                        # Return "UNO"
    else:                                                   # If neither is found in the description (or empty description)...
        return None                                         # The device is NOT a valid dcs

# Returns Arduino UNO Default Pin Map
def uno_pin_map():
    pin_dict = {
      "0": {
        "name": "DP0",
        "direction": "INPUT",                   # INPUT, INPUT_PULLUP, OUTPUT
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "RX - reserved for serial"
      },
      "1": {
        "name": "DP1",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "TX - reserved for serial"
      },
      "2": {
        "name": "DP2",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": True
      },
      "3": {
        "name": "DP3",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": True
      },
      "4": {
        "name": "DP4",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "5": {
        "name": "DP5",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "6": {
        "name": "DP6",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "7": {
        "name": "DP7",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "8": {
        "name": "DP8",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "9": {
        "name": "DP9",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "10": {
        "name": "DP10",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "11": {
        "name": "DP11",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "12": {
        "name": "DP12",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "13": {
        "name": "DP13",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "built-in LED"
      },
      "A0": {
        "name": "AP0",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A1": {
        "name": "AP1",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A2": {
        "name": "AP2",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A3": {
        "name": "AP3",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A4": {
        "name": "AP4",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False,
        "note": "SDA - reserved if using I2C"
      },
      "A5": {
        "name": "AP5",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False,
        "note": "SCL - reserved if using I2C"
      }
    }
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
    pin_dict = {
      "0": {
        "name": "CP0",
        "direction": "INPUT",                   # INPUT, INPUT_PULLUP, OUTPUT
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "RX0 - reserved for serial"
      },
      "1": {
        "name": "CP1",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "TX0 - reserved for serial"
      },
      "2": {
        "name": "DP2",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": True
      },
      "3": {
        "name": "DP3",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": True
      },
      "4": {
        "name": "DP4",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "5": {
        "name": "DP5",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "6": {
        "name": "DP6",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "7": {
        "name": "DP7",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "8": {
        "name": "DP8",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "9": {
        "name": "DP9",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "10": {
        "name": "DP10",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "11": {
        "name": "DP11",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "12": {
        "name": "DP12",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False
      },
      "13": {
        "name": "DP13",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "built-in LED"
      },
        "14": {
        "name": "CP14",
        "direction": "INPUT",            
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "TX3 - reserved for serial"
      },
      "15": {
        "name": "CP15",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "RX3 - reserved for serial"
      },
        "16": {
        "name": "CP16",
        "direction": "INPUT",            
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "TX2 - reserved for serial"
      },
      "17": {
        "name": "CP17",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
        "note": "RX2 - reserved for serial"
      },
      "18": {
        "name": "CP18",
        "direction": "INPUT",            
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": True,
        "note": "TX1 - reserved for serial"
      },
      "19": {
        "name": "CP19",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": True,
        "note": "RX1 - reserved for serial"
      },
      "20": {
        "name": "CP20",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": True,
        "note": "SDA - reserved for I2C"
      },
      "21": {
        "name": "CP21",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": True,
        "note": "SCL - reserved for I2C"
      },
      "22": {
        "name": "DP22",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "23": {
        "name": "DP23",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "24": {
        "name": "DP24",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "25": {
        "name": "DP25",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "26": {
        "name": "DP26",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "27": {
        "name": "DP27",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "28": {
        "name": "DP28",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "29": {
        "name": "DP29",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "30": {
        "name": "DP30",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "31": {
        "name": "DP31",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "32": {
        "name": "DP32",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "33": {
        "name": "DP33",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "34": {
        "name": "DP34",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "35": {
        "name": "DP35",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "36": {
        "name": "DP36",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "37": {
        "name": "DP37",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "38": {
        "name": "DP38",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "39": {
        "name": "DP39",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "40": {
        "name": "DP40",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "41": {
        "name": "DP41",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "42": {
        "name": "DP42",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "43": {
        "name": "DP43",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "44": {
        "name": "DP44",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "45": {
        "name": "DP45",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "46": {
        "name": "DP46",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": True,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "47": {
        "name": "DP47",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "48": {
        "name": "DP48",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "49": {
        "name": "DP49",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "50": {
        "name": "DP50",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "51": {
        "name": "DP51",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "52": {
        "name": "DP52",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "53": {
        "name": "DP53",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": False,
        "interrupt_capable": False,
      },
      "A0": {
        "name": "AP0",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A1": {
        "name": "AP1",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A2": {
        "name": "AP2",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A3": {
        "name": "AP3",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A4": {
        "name": "AP4",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A5": {
        "name": "AP5",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A6": {
        "name": "AP6",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A7": {
        "name": "AP7",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A8": {
        "name": "AP8",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A9": {
        "name": "AP9",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A10": {
        "name": "AP10",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A11": {
        "name": "AP11",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A12": {
        "name": "AP12",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A13": {
        "name": "AP13",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A14": {
        "name": "AP14",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      },
      "A15": {
        "name": "AP15",
        "direction": "INPUT",
        "enabled": False,
        "pwm_capable": False,
        "analog_capable": True,
        "interrupt_capable": False
      }
    }
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

          if file.stem != dcs.get("name"):                      # When opening an existing file, ensure the names match!
              dcs["name"] = file.stem                           # Always ensure the nickname matches the file name

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
        print(f"Unexpected error: {e}")                                         # Print the exception and halt program
        return False                                                            # The DCS JSON was not made (there was an error)

# Delete a dcs JSON from persistent data path for a given controller name
def delete_dcs(data_path, name):
    file_path = data_path / "dcs_info" / f"{name}.json"     # The file path containing all controller JSONs
    try:                                                    # Try to delete the file...
        file_path.unlink()                                  # Delete the file
        return True                                         # The DCS JSON was deleted
    except FileNotFoundError:                               # If the file is not found...
        print(f"No file found for controller: {name}")      # Print error message
        return False                                        # Nothing to delete
    except Exception as e:                                  # If there is another exception...
        print(f"Unexpected error: {e}")                     # Print error message
        return False                                        # The DCS JSON was not deleted

# Rename a controller
def rename_dcs(data_path, old_name, new_name):
  file_path = data_path / "dcs_info" / f"{old_name}.json"     # The file path containing all controller JSONs
  if file_path.is_file():                                     # If there is already a controller/file with that name...
      return False                                            # The controller was not renamed - return false
  else:                                                       # Else -> the new name is available...
      try:                                                    # Attempt to rename the controller
          file_path.rename(new_name)                          # Set new file name
          return True                                         # Controller was renamed, return true
      except FileNotFoundError:                               # If the file does not exist...
          print(f"Error: The file '{old_name}'.json was not found.")
          return False                                        # Return false
      
# Return name of existing JSON file from port
def port_to_name(data_path, port):
    dcs_dir = data_path / "dcs_info"                            # The file path containing all controller JSONs
    for file in dcs_dir.glob("*.json"):                         # Check every JSON in the folder...
        with open(file, 'r') as f:                              # Open each file in read mode...
          dcs = json.load(f)                                    # Load each file in read mode...
        if dcs.get("serial_number") == port["serial_number"]:   # If serial number matches...
          return dcs.get("name")                                # Return the existing JSON file name
    return None                                                 # If none found, return None

# Create dcs dict item for current_dcs from dcs JSON
def create_dict(data_path, port):                           
  name = port_to_name(data_path, port)                      # Get the name of the file/dcs nickname
  if name != None:                                          # If the given port has an associated JSON file (it should already have one)
    file_path = data_path / "dcs_info" / f"{name}.json"     # The file path containing all controller JSONs

    current_dict = {                                        # Create a light weight dictionary entry for the currently active controller
            port_to_name(data_path, port) : {
                "serial_number": port["serial_number"],
                "name": port_to_name(data_path, port)
            }
        }
    return current_dict                                     # Return the current_dict dictionary
  return None                                               # If the dcs has no JSON file, return nothing

# Load a dcs JSON into current_dcs
def load_dcs(data_path, port, current_dcs):
    current_dict = create_dict(data_path, port)
    current_name = port_to_name(data_path, port)
    if current_dict != None:
        if current_name != None:
            current_dcs.update(current_dict)
            return True
    return False

# Remove a dcs JSON from current_dcs
def unload_dcs(data_path, port, current_dcs):
    current_name = port_to_name(data_path, port)
    try:
      return current_dcs.pop(current_name)
    except KeyError:
      print(f"Error: The key '{current_name}' was not found in the dictionary.")
      return False
