# dcs_dict_utils.py
# This file contains the methods needed to describe and load descriptions of dcs into main-thread memory

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON
import textwrap # Allows Arduino C++ code blocks to be dedented
import threading    # Multithreading for Commands Outside of Loop

from . import code_block_utils # Used in clear function at bottom
from . import dcs_script_utils
from . import print_log

# Empty Arduino code for initial flashing event(s)
def_code = textwrap.dedent(f"""                    
            void setup() {{
            // put your setup code here, to run once:
            }}

            void loop() {{
            // put your main code here, to run repeatedly:
            }}
            """)

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
        "pwm_set" : False,                      # Output PWM from software point?
        "int_set" : False,                      # Is the interrupt being used?
        "note": note
    }

# Returns a Data Map for an array
def get_array():   # The defualt software point is always the same
    return {
        "_name" :"",        # Array name, should be the same as key in array dictionary
        "type": "int",      # int, float or bool, and special types (array cast type)
        "size_point": None, # A const point to determine the array size
    }

# Returns a Data Map for a default software point
def get_software_point():   # The defualt software point is always the same
    return {
        "type": "int",      # int, float or bool
        "default" : 1,      # default value
        #"hold" : False,     # is the default value being overriden (serial)?
        #"hold_val" : 1,     # what is the hold value if being held?
        "min_en" : False,   # is the value held at or above a value? (not available for bool)
        "max_en" : False,   # is the value held at or below a value? (not available for bool)
        "min" : 0,          # minimum value (not available for bool)
        "max" : 1,          # maximum value (not available for bool)
        "hardware" : False, # is this pin tied to hardware? (cannot be removed)
        "int_type" : "",    # This specifies what kind of int an int is (eg long int)
        "float_type" : "",  # This specifies what kind of float a float is (eg double) 
        "const" : False     # Is this point a constant?
    }

# Returns a list of software points that correlate with each pin
def get_hardware_points(pin_map, tim_map):

    point_map = {}                  # Point map that will be returned

    # Get hardware points for pins
    for key, val in pin_map.items():
        new_point = get_software_point()
        new_point["type"] = "bool"
        new_point["hardware"] = True
        new_point["_name"] = key

        point_map[key] = new_point

    # Get hardware points for timer registers
    for key, val in tim_map.items():
        
        new_point = get_software_point()        # prescaler
        new_point["type"] = "int"
        new_point["default"] = 0
        new_point["hardware"] = True
        new_point["int_type"] = "uint8_t"
        new_point["_name"] = f"{key}_Prescaler"
        point_map[f"{key}_Prescaler"] = new_point

        new_point = get_software_point()        # preloaded value
        new_point["type"] = "int"
        new_point["default"] = 0
        new_point["hardware"] = True
        new_point["int_type"] = f"uint{tim_map[key]["size_bits"]}_t"
        new_point["_name"] = f"{key}_Preload"
        point_map[f"{key}_Preload"] = new_point

        for k in val["channels"]:
            new_point = get_software_point()    # channel comparisons
            new_point["type"] = "int"
            new_point["default"] = 0
            new_point["hardware"] = True
            new_point["int_type"] = f"uint{tim_map[key]["size_bits"]}_t"
            new_point["_name"] = f"{key}_CH{k}_Comp"
            point_map[f"{key}_CH{k}_Comp"] = new_point

    return point_map                # This map is populated with all needed hardware points

# Returns Arduino UNO Default Pin Map
def uno_pin_map():
    pin_dict = {}

    for i in range(14):
      if i > 1:         # Exclude digital pins 0 and 1 as these are needed by the thread worker!
        pin_dict[f"DP{i}"] = get_pin(f"DP{i}", False, False, False, None)
    
    for i in [3, 5, 6, 9, 10, 11]:
          pin_dict[f"DP{i}"]["pwm_capable"] = True                

    for i in [2, 3]:
        pin_dict[f"DP{i}"]["interrupt_capable"] = True

    for i in range(6):
        pin_dict[f"AP{i}"] = get_pin(f"AP{i}", False, True, False, None)
          
    #pin_dict["DP0"]["note"] = "RX - reserved for serial"   # Exclude digital pins 0 and 1 as these are needed by the thread worker!
    #pin_dict["DP1"]["note"] = "TX - reserved for serial"
    pin_dict["DP13"]["note"] = "built-in LED"
    pin_dict["AP4"]["note"] = "SDA - reserved if using I2C"
    pin_dict["AP5"]["note"] = "SCL - reserved if using I2C"

    return pin_dict



# Returns Arduino UNO Interrupt Map
def uno_int_map():
    int_dict = {
        "DP2": {
            "ISR_name": "ISR2",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP3": {
            "ISR_name": "ISR3",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        #"Timer0_OVF": {
        #    "ISR_name": "TIMER0_OVF_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        #"Timer0_COMPA": {
        #    "ISR_name": "TIMER0_COMPA_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        #"Timer0_COMPB": {
        #    "ISR_name": "TIMER0_COMPB_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        "Timer1_OVF": {
            "ISR_name": "TIMER1_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_COMPA": {
            "ISR_name": "TIMER1_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_COMPB": {
            "ISR_name": "TIMER1_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_CAPT": {
            "ISR_name": "TIMER1_CAPT_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_OVF": {
            "ISR_name": "TIMER2_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_COMPA": {
            "ISR_name": "TIMER2_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_COMPB": {
            "ISR_name": "TIMER2_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
    }
    return int_dict

# Returns Arduino MEGA Default Pin Map
def mega_pin_map():
    pin_dict = {}

    for i in range(54):
      if i > 1:             # Exclude digital pins 0 and 1 as these are needed by the thread worker!
        pin_dict[f"DP{i}"] = get_pin(f"DP{i}", False, False, False, None)
    
    for i in range(2, 14):
            pin_dict[f"DP{i}"]["pwm_capable"] = True 

    for i in range(44, 47):
            pin_dict[f"DP{i}"]["pwm_capable"] = True 

    for i in [2, 3, 18, 19, 20, 21]:
        pin_dict[f"DP{i}"]["interrupt_capable"] = True

    for i in range(16):
        pin_dict[f"AP{i}"] = get_pin(f"AP{i}", False, True, False, None)
          
    #pin_dict["DP0"]["note"] = "RX0 - reserved for serial"  # Exclude digital pins 0 and 1 as these are needed by the thread worker!
    #pin_dict["DP1"]["note"] = "TX0 - reserved for serial"
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
        "DP2": {
            "ISR_name": "ISR2",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP3": {
            "ISR_name": "ISR3",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP18": {
            "ISR_name": "ISR18",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP19": {
            "ISR_name": "ISR19",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP20": {
            "ISR_name": "ISR20",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "DP21": {
            "ISR_name": "ISR21",
            "mode": "LOW",          # LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
            "high": False,          # HIGH is not available on this board
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        #"Timer0_OVF": {
        #    "ISR_name": "TIMER0_OVF_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        #"Timer0_COMPA": {
        #    "ISR_name": "TIMER0_COMPA_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        #"Timer0_COMPB": {
        #    "ISR_name": "TIMER0_COMPB_vect",
        #    "enabled": False,
        #    "blocks": []        # List of code blocks assigned to this ISR
        #},
        "Timer1_OVF": {
            "ISR_name": "TIMER1_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_COMPA": {
            "ISR_name": "TIMER1_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_COMPB": {
            "ISR_name": "TIMER1_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_COMPC": {
            "ISR_name": "TIMER1_COMPC_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer1_CAPT": {
            "ISR_name": "TIMER1_CAPT_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_OVF": {
            "ISR_name": "TIMER2_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_COMPA": {
            "ISR_name": "TIMER2_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer2_COMPB": {
            "ISR_name": "TIMER2_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer3_OVF": {
            "ISR_name": "TIMER3_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer3_COMPA": {
            "ISR_name": "TIMER3_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer3_COMPB": {
            "ISR_name": "TIMER3_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer3_COMPC": {
            "ISR_name": "TIMER3_COMPC_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer3_CAPT": {
            "ISR_name": "TIMER3_CAPT_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer4_OVF": {
            "ISR_name": "TIMER4_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer4_COMPA": {
            "ISR_name": "TIMER4_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer4_COMPB": {
            "ISR_name": "TIMER4_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer4_COMPC": {
            "ISR_name": "TIMER4_COMPC_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer4_CAPT": {
            "ISR_name": "TIMER4_CAPT_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer5_OVF": {
            "ISR_name": "TIMER5_OVF_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer5_COMPA": {
            "ISR_name": "TIMER5_COMPA_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer5_COMPB": {
            "ISR_name": "TIMER5_COMPB_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer5_COMPC": {
            "ISR_name": "TIMER5_COMPC_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
        "Timer5_CAPT": {
            "ISR_name": "TIMER5_CAPT_vect",
            "enabled": False,
            "blocks": []        # List of code blocks assigned to this ISR
        },
    }
    return int_dict

# Returns the template for a timer
def get_timer(timer_name, size_bits, channels, valid_modes, note=None):
    return {
        "name": timer_name,
        "size_bits": size_bits,           # 8 or 16 - defines max count (255 or 65535)
        "enabled": False,
        "prescaler": 0,                   # 0 = stopped, valid: 1, 8, 64, 256, 1024
        "mode": valid_modes[0],           # current selected mode
        "valid_modes": valid_modes,       # UI dropdown + codegen validation
        "channels": {
            ch: {"compare_value": 0}
            for ch in channels
        },
        "preload": 0,                     # written to TCNTn to offset count start
        "note" : note
    }

# Returns the timer dictionary for an uno
def uno_timer_map():
    return {
        #"Timer0": get_timer("Timer0", 8,  ["A", "B"],
        #            ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM"],
        #            note="Used by millis()/delay() - modify with caution"),
        "Timer1": get_timer("Timer1", 16, ["A", "B"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM", "INPUT_CAPTURE"],
                    note="16-bit - good for precise timing"),
        "Timer2": get_timer("Timer2", 8,  ["A", "B"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM"],
                    note="Used by tone()"),
    }

# Returns the timer dictionary for a mega
def mega_timer_map():
    return {
        #"Timer0": get_timer("Timer0", 8,  ["A", "B"],
        #            ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM"],
        #            note="Used by millis()/delay() - modify with caution"),
        "Timer1": get_timer("Timer1", 16, ["A", "B", "C"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM", "INPUT_CAPTURE"],
                    note="16-bit"),
        "Timer2": get_timer("Timer2", 8,  ["A", "B"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM"],
                    note="Used by tone()"),
        "Timer3": get_timer("Timer3", 16, ["A", "B", "C"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM", "INPUT_CAPTURE"],
                    note="16-bit"),
        "Timer4": get_timer("Timer4", 16, ["A", "B", "C"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM", "INPUT_CAPTURE"],
                    note="16-bit"),
        "Timer5": get_timer("Timer5", 16, ["A", "B", "C"],
                    ["OVF", "CTC", "FAST_PWM", "PHASE_CORRECT_PWM", "INPUT_CAPTURE"],
                    note="16-bit"),
    }

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
        tim_map = uno_timer_map()
        fqbn = "arduino:avr:uno"
    elif dcs_type == "MEGA":                    # If the board is an MEGA, assign the pin and interrupt maps for MEGA
        pin_map = mega_pin_map()
        int_map = mega_int_map()
        tim_map = mega_timer_map()
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
    "software_points": get_hardware_points(pin_map, tim_map),
    "int_config": int_map,
    "timers" : tim_map,
    "arrays" : {},                      # By default there are no arrays on start-up, they can be added
    "setup_blocks" : [],                # Code blocks for different parts of the program
    "loop_blocks" : [],
    "sample_time" : 1                   # Time between samples in seconds
    }

    # A copy of the Arduino Default code so the controller can be flashed initially
    
    try:                                                                        # Try to write this JSON as a file
        file_path = data_path / "dcs_info" / f"{controller_name}.json"          # File path to dcs JSON files
        with open(file_path, 'w') as dcs_file:                                  # Open the file path and write
            json.dump(dcs_dict, dcs_file, indent=4)                             # JSON dump the dictionary for this controller
        
        dcs_script_utils.create_Script(data_path, controller_name, def_code)
        with current_dict_lock:
            add_current_dict(current_dict, data_path, controller_name)

        return True                                                             # The DCS JSON was made and the ino

    except Exception as e:                                                      # If an exception is caught...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                            # The DCS JSON was not made (there was an error)

# Create an empty dcs JSON (used to save and load programs), will not have controller specific data
def init_code_dcs(data_path, current_dict, current_dict_lock):
    
                                                                # Find the next available controller index
    dcs_dir = data_path / "dcs_info"                            # The file path containing all controller JSONs
    existing = list(dcs_dir.glob("unnamed_program_*.json"))     # Find all unnamed controllers
    n = len(existing)                                           # Next gaurenteed unnamed controller index
    controller_name = f"unnamed_program_{n}"                    # Use the controller index to generate the file/nick-name

    pin_map = mega_pin_map()                                    # Choose MEGA dcs maps because they contain all possible points
    int_map = mega_int_map()                                    # Note only MEGA has Timer 1C so if used it cannot be loaded into UNO
    tim_map = mega_timer_map()

                                                # Create a JSON Dictionary that contains the default controller configuration
    dcs_dict = {                                # Default Controller Setings:
    "description": None,
    "hwid": None,
    "manufacturer":None,
    "serial_number": None,
    "port": None,      
    "vid": None,
    "pid": None,
    "name": controller_name,
    "fqbn": None,
    "pin_config": mega_pin_map(),
    "software_points": get_hardware_points(pin_map, tim_map),
    "int_config": int_map,
    "timers" : tim_map,
    "arrays" : {},                      # By default there are no arrays on start-up, they can be added
    "setup_blocks" : [],                # Code blocks for different parts of the program
    "loop_blocks" : []
    }
    
    try:                                                                        # Try to write this JSON as a file
        file_path = data_path / "dcs_info" / f"{controller_name}.json"          # File path to dcs JSON files
        with open(file_path, 'w') as dcs_file:                                  # Open the file path and write
            json.dump(dcs_dict, dcs_file, indent=4)                             # JSON dump the dictionary for this controller
        
        dcs_script_utils.create_Script(data_path, controller_name, def_code)
        with current_dict_lock:
            add_current_dict(current_dict, data_path, controller_name)
        
        load_prog(data_path, controller_name, current_dict, current_dict_lock)

        return True                                                             # The DCS JSON was made and the ino

    except Exception as e:                                                      # If an exception is caught...
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False                                                            # The DCS JSON was not made (there was an error)

# Determine if JSON is for code controller (empty port data) - takes controller JSON directly
def is_prog(cont):
    if cont["description"] == None and cont["hwid"] == None and cont["manufacturer"] == None:   # Does not check all fields but good enough to know if its empty
        return True
    return False

# Delete a dcs JSON from persistent data path for a given controller name
def delete_dcs(data_path, name, current_dcs, current_dict, current_dict_lock):
    file_path = data_path / "dcs_info" / f"{name}.json"                   # The file path containing all controller JSONs
    try:                                                                  # Try to delete the file...
        unload_dcs(data_path, name_to_port(data_path, name),current_dcs); # Unload the old (defunct) data-structure
        file_path.unlink()                                                # Delete the file

        script_path = data_path / pathlib.Path("dcs_scripts")
        dcs_script_utils.remove_Script(script_path, name)

        with current_dict_lock:
            del current_dict[name]

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

# Load a dcs JSON into current_dcs by port, will not work for code
def load_dcs(data_path, port, current_dcs, current_dict, current_dict_lock):
    current_dict = create_dict(data_path, port)
    current_name = port_to_name(data_path, port)
    if current_dict != None:
        if current_name != None:
            current_dcs.update(current_dict)

            script_path = data_path / "dcs_scripts" / current_name
            if not script_path.exists():
                dcs_script_utils.create_Script(data_path, current_name, def_code)

            with current_dict_lock:
                add_current_dict(current_dict, data_path, current_name)

            return True
    return False

# Load a program into the currrent dict, they can be distinguished because they are empty
def load_prog(data_path, prog_name, current_dict, current_dict_lock):
    file_path = data_path / "dcs_info" / f"{prog_name}.json"    # Get the data-path of the relevant info json file
    with open(file_path, 'r') as f:                             # Open the json file (read only) as f
        prog = json.load(f)                                     # Load the json data from this file

    with current_dict_lock:
        current_dict[prog_name] = prog                          # Load the program into the current_dict
        return True
    return False

# Load all programs into the current-dcs (run at start of main program)
def load_progs(current_dict, current_dict_lock, datapath):

    for key in current_dict:
        if is_prog(current_dict[key]):
            load_prog(datapath, key, current_dict, current_dict_lock)  # This needs no return type

# Remove a program from the current_dcs by name
def unload_prog(prog_name, current_dict, current_dict_lock):
    with current_dict_lock:
        del current_dict[prog_name]
        return True

# Remove a dcs JSON from current_dcs by port
def unload_dcs(data_path, port, current_dcs):
    current_name = port_to_name(data_path, port)
    try:
      return current_dcs.pop(current_name)
    except KeyError:
      print_log.pL("System", "Error", f"The key '{current_name}' was not found in the dictionary.", "System", True, None)
      return False

# Rename a controller or code
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
        was_loaded = old_name in current_dcs
        if was_loaded:
            port = name_to_port(data_path, old_name)
            unload_dcs(data_path, port, current_dcs)                          # Unload the old (defunct) data-structure

        file_path.rename(new_path)                                            # Rename the old file to the new files
        with open(new_path, 'r') as f:                                        # Open the renamed file as f (read only)
          dcs = json.load(f)                                                  # Load the json from f as dcs
        dcs["name"] = new_name                                                # Update the name inside of dcs
        with open(new_path, 'w') as f:                                        # With the new file open (write) as f
          json.dump(dcs, f, indent=4)                                         # Write dcs to f, this ensures the file updates

        if is_prog(current_dict[old_name]) == False:                          # If the old (and thus new) controller was not a program
            dcs_script_utils.rename_Script(data_path, old_name, new_name)     # Rename the script associated with it

            if was_loaded:                                                                  # If the controller was loaded when the name was changed...
                port = name_to_port(data_path, new_name)
                load_dcs(data_path, port, current_dcs, current_dict, current_dict_lock);    # Load in the new data-structure

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

# Get a saved JSON file from directory
def get_dict(data_path, name):
    
    json_file = pathlib.Path(data_path) / "dcs_info" / f"{name}.json"
    
    if not json_file.exists():
        print_log.pL("System", "Error", f"JSON file '{name}' not found.", "System", True, None)
        return None
    
    with json_file.open("r", encoding="utf-8") as f:
        return json.load(f)
    
    return None

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
            change_point_type(pin_dict, point_dict, pin, "int", True)
            pin_dict[pin]["min_en"] = True
            pin_dict[pin]["max_en"] = True
            pin_dict[pin]["max"] = 0
            pin_dict[pin]["max"] = 1023
        else:
            change_point_type(pin_dict, point_dict, pin, "bool", True)
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

def change_pin_pwm(pin_dict, pin, point_dict, enable):
    if not pin_dict[pin]["pwm_capable"]:
        return False

    if enable:
        print("test1")
        change_pin_dir(pin_dict, pin, "OUTPUT")
        change_point_type(pin_dict, point_dict, pin, "int", True)
        point_dict[pin]["min_en"] = True
        point_dict[pin]["max_en"] = True
        point_dict[pin]["max"] = 0
        point_dict[pin]["max"] = 255
        pin_dict[pin]["pwm_set"] = True
    else:
        print("test2")
        change_pin_dir(pin_dict, pin, "INPUT")
        change_point_type(pin_dict, point_dict, pin, "bool", True)
        point_dict[pin]["min_en"] = False
        point_dict[pin]["max_en"] = False
        point_dict[pin]["max"] = 0
        point_dict[pin]["max"] = 1
        pin_dict[pin]["pwm_set"] = False
    return True

def change_pin_int(pin_dict, pin, val, int_map):

    if pin_dict[pin]["pwm_set"]:
        return False

    if pin_dict[pin]["interrupt_capable"]:
        pin_dict[pin]["int_set"] = val
        if val:
            change_pin_dir(pin_dict, pin, "INPUT")

        # Set the actual interrupt!
        int_map[pin]["enabled"] = val
        
        return True
    return False

def change_sample_time(current_dict, cont_name, sample_time):

    if cont_name not in current_dict:
        return False
    
    if is_prog(current_dict[cont_name]):
        return False

    try:
        current_dict[cont_name]["sample_time"] = float(sample_time)
        return True
    except ValueError:
        return False

# === Functions to change point settings ===

# Ensure if a point's value is being changed, it does not break prescalers!
def val_prescale(point_name, value):
    if "Prescaler" in point_name:
        if value in [0, 1, 8, 64, 256, 1024]:
            return True
        return False
    return True

# Ensure if a point's value is being changed, it does not break timer registers!
def val_timer_reg(point_name, value, tim_dict):
    # Only applies to compare and preload values, not prescaler
    if "Prescaler" in point_name:
        return True
    
    # Extract timer name, first token before underscore e.g. "Timer1" from "Timer1_CHA_Comp"
    timer_name = point_name.split('_')[0]
    
    if timer_name not in tim_dict:
        return True                  
    
    max_val = (2 ** tim_dict[timer_name]["size_bits"]) - 1
    return 0 <= value <= max_val

# Run both timer checks
def val_timer(point_name, value, tim_dict):
    return val_prescale(point_name, value) and val_timer_reg(point_name, value, tim_dict)

def change_point_name(pin_dict, point_dict, old_name, new_name): 
    if old_name not in point_dict:
        return False
    if point_dict[old_name]["hardware"]:
        return False
    if new_name in point_dict:
        return False
    point_dict[new_name] = point_dict[old_name]
    point_dict[new_name]["_name"] = new_name
    del point_dict[old_name]
    return True

# Change the int type of a point
def set_point_int_type(point_dict, point_name, str):
    if point_dict[point_name]["type"] == "int":         # This can only be set if the point is an integer
        if is_int_type(str):
            point_dict[point_name]["int_type"] = str
            return True
    return False

# Display a formatted string of all int types (for the help menu)
def show_int_types():
    return f"""
    An Extremely Incomplete list of C++ Integer Types (for reference)

    Standard Int Types (Signed and Unsigned):
    int
    signed / signed int
    unsigned / unsigned int
    short / short int
    long / long int
    long long / long long int

    Fixed-Width Int Types:
    int8_t / uint8_t (byte)
    int16_t / uint16_t (word)
    int32_t / uint32_t
    int64_t / uint64_t

    Special and Utility Int Types:
    char / wchar_t
    size_t
    ptrdiff_t
    """

# Determines if a string (eg "uint8_t") is a valid int type
def is_int_type(s):
    tokens = s.strip().split()

    if not tokens:
        return False

    # Single-token special / typedef types
    single_types = {
        "int", "char", "wchar_t",
        "int8_t", "int16_t", "int32_t", "int64_t",
        "uint8_t", "uint16_t", "uint32_t", "uint64_t",
        "ptrdiff_t", "size_t",
        "byte", "word"
    }

    if len(tokens) == 1:
        return tokens[0] in single_types or tokens[0] in {"signed", "unsigned"}

    # Allowed specifiers
    sign = {"signed", "unsigned"}
    size = {"short", "long"}
    base = {"int"}

    sign_count = 0
    short_count = 0
    long_count = 0
    int_count = 0

    for t in tokens:
        if t in sign:
            sign_count += 1
        elif t == "short":
            short_count += 1
        elif t == "long":
            long_count += 1
        elif t == "int":
            int_count += 1
        else:
            return False  # unknown token

    # Rules based on C++ specifiers:

    # Only one sign allowed
    if sign_count > 1:
        return False

    # Can't mix short and long
    if short_count > 0 and long_count > 0:
        return False

    # short appears at most once
    if short_count > 1:
        return False

    # long can appear once or twice (long long)
    if long_count > 2:
        return False

    # If long appears twice, it's "long long"
    if long_count == 2 and short_count > 0:
        return False

    # int can appear at most once
    if int_count > 1:
        return False

    # At least one meaningful type specifier must exist
    if short_count == 0 and long_count == 0 and int_count == 0:
        return False

    return True

# Determines if a string (eg "long double") is a valid float type
def is_float_type(s):
    tokens = s.strip().split()

    if not tokens:
        return False

    # Standard C++ floating point base types
    # Arduino note: on most 8-bit Arduinos, 'double' is the same as 'float'
    base_floats = {"float", "double"}

    # 1. Handle single-token types
    if len(tokens) == 1:
        return tokens in base_floats

    # 2. Handle multi-token types (e.g., "long double")
    # Allowed specifiers for floats
    long_count = 0
    double_count = 0

    for t in tokens:
        if t == "long":
            long_count += 1
        elif t == "double":
            double_count += 1
        else:
            # "signed", "unsigned", "short", or "int" are invalid for floats
            return False 

    # Rules based on C++ specifiers:
    
    # Only "long double" is a valid multi-token float type
    if long_count == 1 and double_count == 1 and len(tokens) == 2:
        return True
    
    # "long long double" or "long float" are not valid C++
    return False

def add_point(point_dict, name):
    if name in point_dict:  # dict membership checks keys directly
        return False
    point_dict[name] = get_software_point()
    point_dict[name]["_name"] = name
    return True

def rem_point(current_dict, cont_name, point_name):
    # 1. Controller Existence Check
    if cont_name not in current_dict:
        # This prevents indexing current_dict[cont_name] if the name is wrong
        return False
        
    # 2. Get the points dictionary for THIS controller
    points = current_dict[cont_name].get("software_points")
    if points is None or point_name not in points:
        return False

    # 3. Hardware check: Use .get() to be safe
    point_data = points[point_name]
    
    # If point_data is not a dict (which would happen if JSON is corrupted), 
    # it would cause the "string indices" error. We check type first.
    if isinstance(point_data, dict) and point_data.get("hardware") == False:
        
        # 4. CRITICAL: Cleanup blocks while the point still exists
        # If you delete it before calling this, the cleanup can't verify the point
        rem_point_from_blocks(point_name, current_dict, cont_name)
        
        # 5. Now delete from master list
        del points[point_name]
        return True
        
    return False

def rem_point_from_blocks(point_name, current_dict, cont_name):
    # This returns a dict like {'setup_blocks': [...], 'loop_blocks': [...]}
    block_lists_dict = code_block_utils.find_lists(current_dict, cont_name)
    
    # FIX: Iterate over .values() to get the actual lists, not the string keys
    for block_list in block_lists_dict.values():
        if not isinstance(block_list, list):
            continue
            
        for block_inst in block_list:
            # Safety check: ensure we have a dictionary block
            if not isinstance(block_inst, dict):
                continue

            # Clean Input Points: use list(keys) to allow deletion during loop
            inputs = block_inst.get("input_points", {})
            for key in list(inputs.keys()):
                p_conf = inputs[key]
                # Match by name string
                if isinstance(p_conf, dict) and p_conf.get("_name") == point_name:
                    del inputs[key]
            
            # Clean Output Points
            outputs = block_inst.get("output_points", {})
            for key in list(outputs.keys()):
                p_conf = outputs[key]
                if isinstance(p_conf, dict) and p_conf.get("_name") == point_name:
                    del outputs[key]

            # Clean conditional point
            condition = block_inst.get("condition")
            if condition is not None and condition.get("_name") == point_name:
                code_block_utils.rem_condition(block_inst)

def change_point_const(point_dict, point, value, array_dict):
    if point in point_dict:

        for key in array_dict:
            if array_dict[key]["size_point"] is point:
                return False

        if point_dict[point]["hardware"]:
            return False
        
        if value:
            point_dict[point]["min_en"] = False
            point_dict[point]["max_en"] = False
            #point_dict[point]["hold"] = False
        
        point_dict[point]["const"] = value
        return True
    
    return False


def change_point_type(pin_dict, point_dict, point, type, auth): # Auth to change hardware point type - DO NOT GIVE TO USER
    if point in point_dict:

        if auth == False and point_dict[point]["hardware"]:
            return False

        if type in ["int", "float", "bool"]:
            point_dict[point]["type"] = type
            if type == "bool":
                point_dict[point]["int_type"] = {}
                point_dict[point]["float_type"] = {}
                if pin_dict.get(point, {}).get("analog_set", False):
                    return False
                point_dict[point]["min_en"] = False
                point_dict[point]["max_en"] = False
                point_dict[point]["max"] = 1
                point_dict[point]["min"] = 0
                #if point_dict[point]["hold_val"] > 0:
                #    point_dict[point]["hold_val"] = 1
                if point_dict[point]["default"] > 0:
                    point_dict[point]["default"] = 1
            if type == "int":
                point_dict[point]["float_type"] = {}
                #point_dict[point]["hold_val"] = int(point_dict[point]["hold_val"])
                point_dict[point]["min"] = int(point_dict[point]["min"])
                point_dict[point]["max"] = int(point_dict[point]["max"])
            if type == "float":
                point_dict[point]["int_type"] = {}
                if pin_dict.get(point, {}).get("analog_set", False):
                    return False
                #point_dict[point]["hold_val"] = float(point_dict[point]["hold_val"])
                point_dict[point]["min"] = float(point_dict[point]["min"])
                point_dict[point]["max"] = float(point_dict[point]["max"])
            return True
    return False

# Function that allows the special type (eg long long int) of a point to be changed
def change_point_spec_type(point_dict, point, spec_type):
    if point in point_dict:

        if point_dict[point]["hardware"]:   # Do not allow hardware points to be assigned special types
            return False

        if spec_type == "None" or spec_type == "none" or spec_type == None:
            point_dict[point]["int_type"] = ""
            point_dict[point]["float_type"] = ""
            return True

        if point_dict[point]["type"] == "int":
            if is_int_type(spec_type):
               point_dict[point]["int_type"] = spec_type
               point_dict[point]["float_type"] = ""
               return True 

        if point_dict[point]["type"] == "float":
            if is_float_type(spec_type):
               point_dict[point]["int_type"] = ""
               point_dict[point]["float_type"] = spec_type
               return True 
             
    return False

def change_point_def(point_dict, point, value, tim_dict):
    if point not in point_dict:
        return False
    
    if val_timer(point, value, tim_dict) == False:
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

# def change_point_hold_val(point_dict, point, value, tim_dict):
#     if point not in point_dict:
#         return False
    
#     if val_timer(point, value, tim_dict) == False:
#         return False
    
#     if point_dict[point]["const"]:
#         return False

#     point_type = point_dict[point]["type"]
    
#     if point_type == "bool":
#         if not isinstance(value, bool) and value not in [0, 1]:
#             return False
#     elif point_type == "int":
#         if not isinstance(value, (int, float)) or isinstance(value, bool):
#             return False
#         value = int(value)  # coerce float to int if needed
#     elif point_type == "float":
#         if not isinstance(value, (int, float)) or isinstance(value, bool):
#             return False
#         value = float(value)  # coerce int to float if needed
    
#     # Check min/max bounds if enabled
#     if point_dict[point].get("min_en") and value < point_dict[point]["min"]:
#         return False
#     if point_dict[point].get("max_en") and value > point_dict[point]["max"]:
#         return False
    
#     point_dict[point]["hold_val"] = value
#     if point_dict[point]["type"] == "int":
#         point_dict[point]["hold_val"] = int(value)
#     return True

# def change_point_hold_en(point_dict, point, value):
#     if not isinstance(value, bool):
#         return False
    
#     if point_dict[point]["const"]:
#         return False

#     if point in point_dict:
#         point_dict[point]["hold"] = value
#         return True
#     return False

def change_point_min_en(point_dict, point, value):
    if not isinstance(value, bool):
        return False
    if point_dict[point]["hardware"] == True:   # User cannot change hardware settings
        return False
    
    if point_dict[point]["const"]:
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
    if point_dict[point]["hardware"] == True:   # User cannot change hardware settings
        return False
    
    if point_dict[point]["const"]:
        return False

    if point in point_dict:
        if point_dict[point]["type"] == "bool":
            return False
        point_dict[point]["max_en"] = value
        return True
    return False

def change_point_min(point_dict, point, value, tim_dict):
    if point not in point_dict:
        return False
    
    if point_dict[point]["const"]:
        return False

    if val_timer(point, value, tim_dict) == False:
        return False

    if point_dict[point]["type"] == "bool":
        return False
    if point_dict[point]["hardware"] == True:   # User cannot change hardware settings
        return False
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    if point_dict[point]["max_en"] and value > point_dict[point]["max"]:
        return False
    point_dict[point]["min"] = value
    if point_dict[point]["type"] == "int":
        point_dict[point]["min"] = int(value)
    return True

def change_point_max(point_dict, point, value, tim_dict):
    if point not in point_dict:
        return False
    
    if point_dict[point]["const"]:
        return False

    if val_timer(point, value, tim_dict) == False:
        return False

    if point_dict[point]["type"] == "bool":
        return False
    if point_dict[point]["hardware"] == True:   # User cannot change hardware settings
        return False
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    if point_dict[point]["min_en"] and value < point_dict[point]["min"]:
        return False
    point_dict[point]["max"] = value
    if point_dict[point]["type"] == "int":
        point_dict[point]["max"] = int(value)
    return True

# Returns point_dict, only enabled pins if active is true
def list_pins(pin_dict, active):
    if active:
        active_dict = {}
        for key in pin_dict:
            if pin_dict[key]["enabled"]:
                active_dict[key] = pin_dict[key]
        return active_dict
    else:
        return pin_dict
    
# Returns all software points and active hardware points
def list_points(pin_dict, point_dict, tim_dict):
    active_dict = {}
    for key, val in point_dict.items():

        if not val["hardware"]:                     # software point are always active
            active_dict[key] = val

        elif key in pin_dict:                       # pin hardware point
            if pin_dict[key]["enabled"]:
                active_dict[key] = val

        else:                                       # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in tim_dict and tim_dict[timer_name]["enabled"]:
                active_dict[key] = val
            
    return active_dict


# === Timer Setting Functions ===

def set_timer_enable(tim_dict, timer_name, value, int_dict):
    if not isinstance(value, bool):
        return False

    if timer_name not in tim_dict:
        return False
    
    timer = tim_dict[timer_name]
    timer["enabled"] = value

    if value:
        set_timer_ints(tim_dict, timer_name, timer["mode"], int_dict)   # ensure the interrupts get updated when the clock is enabled
    else: 
        for key in int_dict:
            if key.startswith(timer_name):
                int_dict[key]["enabled"] = False                        # Disable vectors if timer is disabled (so they do not clutter code space)

    return True

# Allows timer mode to be changed
# 8-bit: OVF, CTC, FAST_PWM, PHASE_CORRECT_PWM ; 16-bit: INPUT_CAPTURE
def set_timer_mode(tim_dict, timer_name, mode, int_dict):
    if timer_name not in tim_dict:
        return False
    
    if tim_dict[timer_name]["enabled"] == False:
        return False

    timer = tim_dict[timer_name]
    
    if mode not in timer["valid_modes"]:
        return False
    
    timer["mode"] = mode
    set_timer_ints(tim_dict, timer_name, mode, int_dict)
    return True

# Manages enable/disable state for timer interrupts
def set_timer_ints(tim_dict, timer_name, mode, int_dict):
    if mode == "OVF":
        for key in int_dict:
            if key == f"{timer_name}_OVF":
                int_dict[key]["enabled"] = True
            elif key.startswith(f"{timer_name}_COMP"):
                int_dict[key]["enabled"] = False
            elif key.startswith(f"{timer_name}_CAPT"):
                int_dict[key]["enabled"] = False
    elif mode == "CTC":
        for key in int_dict:
            if key == f"{timer_name}_OVF":
                int_dict[key]["enabled"] = False
            elif key.startswith(f"{timer_name}_COMP"):
                int_dict[key]["enabled"] = True
            elif key.startswith(f"{timer_name}_CAPT"):
                int_dict[key]["enabled"] = False
    elif mode == "INPUT_CAPTURE":
        for key in int_dict:
            if key == f"{timer_name}_CAPT":
                int_dict[key]["enabled"] = True
            elif key.startswith(timer_name):
                int_dict[key]["enabled"] = False
    else:  # FAST_PWM, PHASE_CORRECT_PWM
        for key in int_dict:
            if key.startswith(timer_name):
                int_dict[key]["enabled"] = True


# === Interrupt Setting Functions ===

def set_int_enable(int_config, int_name, value):
    if not isinstance(value, bool):
        return False

    if int_name not in int_config:
        return False
    
    if int_name.startswith("DP"):                   # Only change interrupt enable if its a pin triggered interrupt!
        int_config[int_name]["enabled"] = value
        return True

def set_int_mode(int_config, int_name, mode):
    if int_name not in int_config:
        return False
    
    intr = int_config[int_name]

    if int_name.startswith("DP"):                           # If the interrupt is from a digital pin
        if mode in ["LOW", "CHANGE", "RISING", "FALLING"]:
            intr["mode"] = mode
            return True
        elif mode == "HIGH" and intr["high"]:               # Check if the board supports this interrupt mode
            intr["mode"] = mode
            return True

    return False


def add_array(array_dict, name):
    if name not in array_dict:
        array_dict[name] = get_array()
        array_dict[name]["_name"] = name
        return True
    return False

def rem_array(array_dict, name):
    if name in array_dict:
        del array_dict[name]
        return True
    return False

def ren_array(array_dict, old_name, new_name):
    if new_name not in array_dict and old_name in array_dict:
        array_dict[new_name] = array_dict[old_name]
        array_dict[new_name]["_name"] = new_name
        del array_dict[old_name]
        return True
    return False

def edit_array_type(array_dict, name, type_str):
    if name in array_dict:
        if type in ["int", "bool", "float"]:
            array_dict[name]["type"] = type_str
            return True
        elif is_float_type(type_str) or is_int_type(type_str):
            array_dict[name]["type"] = type_str
            return False
        
        return False
    return False

def add_array_const(array_dict, array_name, point_dict, point_name):
    if array_name in array_dict and point_name in point_dict:
        if array_dict[array_name]["size_point"] == None:
            if point_dict[point_name]["const"]:
                array_dict[array_name]["size_point"] = point_dict[point_name]
                return True
            return False
        return False
    return False

def rem_array_const(array_dict, array_name):
    if array_name in array_dict:
        array_dict[array_name]["size_point"] = None
        return True
    return False

# Load program from controller
def load_cont_to_prog(data_path, cont_name, prog_list, prog_name):

    cont = get_dict(data_path, cont_name)

    if cont == None:
        print_log.pL("System", "Error", f"Controller {cont_name} not found", "System", "True", None)
        return False

    if prog_name in prog_list:
            print_log.pL("System", "Event", f"Loading Controller {cont_name} into Program {prog_name}", "System", "True", None)
    else: 
        print_log.pL("System", "Error", f"Program {prog_name} not found", "System", "True", None)
        return False
    
    clear_controller(prog_list, prog_name)

    for key in cont["pin_config"]:                                                                          # For each pin in the program pin-map...
        for key_p in prog_list[prog_name]["pin_config"]:                                                    # Check each pin in the controller
            if prog_list[prog_name]["pin_config"][key_p]["name"] == cont["pin_config"][key]["name"]:        # If the pins are the same...   
                prog_list[prog_name]["pin_config"][key_p] = cont["pin_config"][key]

    for key in cont["int_config"]:     
        for key_p in prog_list[prog_name]["int_config"]:                                                        # Check each int in the controller
            if prog_list[prog_name]["int_config"][key_p]["ISR_name"] == cont["int_config"][key]["ISR_name"]:    # If the ints are the same...
                prog_list[prog_name]["int_config"][key_p] = cont["int_config"][key]
                                                                                                
    for key in cont["software_points"]:
        for key_p in prog_list[prog_name]["software_points"]:
            if prog_list[prog_name]["software_points"][key_p]["_name"] == cont["software_points"][key]["_name"]:
                prog_list[prog_name]["software_points"][key_p] = cont["software_points"][key]

    for key in cont["arrays"]:
        prog_list[cont_name]["arrays"][key] = cont["arrays"][key]

    for key in cont["timers"]:
        if cont["timers"][key]["enabled"]:
            prog_list[prog_name]["timers"][key]["enabled"] = True

    cont_block_lists = code_block_utils.find_lists_saved(data_path, cont_name)               # Find all block lists in program
    prog_block_lists = code_block_utils.find_lists(prog_list, prog_name)                     # Find all block lists in controller

    for key_i in prog_block_lists:                                                  
        for key_j in cont_block_lists:     
            if key_i == key_j:     
                prog_block_lists[key_i].clear()
                prog_block_lists[key_i].extend(cont_block_lists[key_j])

    return True


# Load program into controller
def load_prog_to_cont(cont_name, prog_name, cont_list, data_path):

    if cont_name in cont_list:
        print_log.pL("System", "Event", f"Loading Program {prog_name} into Controller {cont_name}", "System", "True", None)
    else: 
        print_log.pL("System", "Error", f"Controller {cont_name} not found", "System", "True", None)
        return False

    prog = get_dict(data_path, prog_name)

    if prog == None:
        print_log.pL("System", "Error", f"Program {prog_name} not found", "System", "True", None)
        return False

    # CHECK COMPATABILITY FIRST!

    for key in prog["pin_config"]:                                                                          # For each pin in the program pin-map...
        if prog["pin_config"][key]["enabled"]:                                                              # If the pin is in use...
            matched = False
            for key_p in cont_list[cont_name]["pin_config"]:                                                # Check each pin in the controller
                if cont_list[cont_name]["pin_config"][key_p]["name"] == prog["pin_config"][key]["name"]:    # If the pins are the same...
                    matched = True
            if matched == False:
                print_log.pL("System", "Error", f"Program {prog_name} has pins not found in Controller {cont_name}", "System", "True", None)                                                                                                # Break out of the loop
                return False                                                                                # If loop completes without match, code is not compattible with controller 

    # If the code gets to this point, all points are compattible!  
    for key in prog["int_config"]:                                                                              # For each int in the program pin-map...
        if prog["int_config"][key]["enabled"]:                                                                  # If the int is in use...
            matched = False
            for key_p in cont_list[cont_name]["int_config"]:                                                    # Check each int in the controller
                if cont_list[cont_name]["int_config"][key_p]["ISR_name"] == prog["int_config"][key]["ISR_name"]:# If the ints are the same...
                    matched = True
            if matched == False:
                print_log.pL("System", "Error", f"Program {prog_name} has interrupts not found in Controller {cont_name}", "System", "True", None)                                                                                                # Break out of the loop
                return False       

    # If the code gets to this point, all interrupts are compattible!  
    # Direct comparrisson of timers would always fail because Timer 1 has 3 channels on MEGA and 2 channels on UNO, check points instead!
    # First get all points in the program
    prog_points = list_points(prog["pin_config"],prog["software_points"], prog["timers"])
    
    # Remove all software points from prog_points -> soft_points, they do not need to be checked
    hard_points = {}
    for key in prog_points:
        if prog_points[key]["hardware"]:
            hard_points[key] = prog_points[key]

    print(hard_points)

    for key in hard_points:                                                                             # None of these will be software points
        matched = False

        for key_p in cont_list[cont_name]["software_points"]:                                           # Any software point here will not match
            if prog_points[key]["_name"] == cont_list[cont_name]["software_points"][key_p]["_name"]:    # This match must be a hardware point (pin or register)
                matched = True

        if matched == False:
            print_log.pL("System", "Error", f"Program {prog_name} has points not found in Controller {cont_name}", "System", "True", None)                                                                                                # Break out of the loop
            return False 

    # Finally just make sure timers match (enabled ones)
    for key in prog["timers"]:
        matched = False
        if prog["timers"][key]["enabled"]:
            if cont_list[cont_name]["timers"][key]:
                matched = True
        else:                                           # If the timer is not enabled..
            matched =  True                             # There is no need to check it
        if matched == False:
            print_log.pL("System", "Error", f"Program {prog_name} has timers not found in Controller {cont_name}", "System", "True", None)
            return False

    # At this point, the programs are known to be compattible, we can start loading the program!
    clear_controller(cont_list, cont_name)

    for key in prog["pin_config"]:                                                                          # For each pin in the program pin-map...
        if prog["pin_config"][key]["enabled"]:                                                              # If the pin is in use...
            for key_p in cont_list[cont_name]["pin_config"]:                                                # Check each pin in the controller
                if cont_list[cont_name]["pin_config"][key_p]["name"] == prog["pin_config"][key]["name"]:    # If the pins are the same...
                    cont_list[cont_name]["pin_config"][key_p] = prog["pin_config"][key]

    for key in prog["int_config"]:                                                                              # For each int in the program pin-map...
        if prog["int_config"][key]["enabled"]:                                                                  # If the int is in use...
            for key_p in cont_list[cont_name]["int_config"]:                                                    # Check each int in the controller
                if cont_list[cont_name]["int_config"][key_p]["ISR_name"] == prog["int_config"][key]["ISR_name"]:# If the ints are the same...
                    cont_list[cont_name]["int_config"][key_p] = prog["int_config"][key]

    for key in prog_points:
        cont_list[cont_name]["software_points"][key] = prog_points[key]

    for key in prog["timers"]:
        if prog["timers"][key]["enabled"]:
            cont_list[cont_name]["timers"][key]["enabled"] = True

    for key in prog["arrays"]:
        cont_list[cont_name]["arrays"][key] = prog["arrays"][key]

    prog_block_lists = code_block_utils.find_lists_saved(data_path, prog_name)               # Find all block lists in program
    cont_block_lists = code_block_utils.find_lists(cont_list, cont_name)                     # Find all block lists in controller

    for key_i in prog_block_lists:                                                      
        for key_j in cont_block_lists:
            if key_i == key_j:
                cont_block_lists[key_j].clear()
                cont_block_lists[key_j].extend(prog_block_lists[key_i])

    return True

# Reduces the timer1 implementation of a program to be Uno compatible
def reduce_Timer1(current_dict, prog_name):
    if is_prog(current_dict[prog_name]) == False:
        return False

    if "Timer1_CHC_Comp" in current_dict[prog_name]["software_points"]:
        if "Timer1_COMPC" in current_dict[prog_name]["int_config"]:
            del current_dict[prog_name]["int_config"]["Timer1_COMPC"]
            rem_point(current_dict, prog_name, "Timer1_CHC_Comp")
            del current_dict[prog_name]["timers"]["Timer1"]["channels"]["C"]
            return True
    return False

# Expands the timer1 implementation of a program to be Mega complete
def expand_Timer1(current_dict, prog_name):
    if is_prog(current_dict[prog_name]) == False:
        return False

    if "Timer1_CHC_Comp" in current_dict[prog_name]["software_points"]:
        return False
    
    if "Timer1_COMPC" in current_dict[prog_name]["int_config"]:
        return False
    
    # Add the channel back to the timer
    current_dict[prog_name]["timers"]["Timer1"]["channels"]["C"] = {"compare_value": 0}

    # Add the channel C interrupt back (Timer1_COMPC)
    current_dict[prog_name]["int_config"]["Timer1_COMPC"] = {
        "ISR_name": "TIMER1_COMPC_vect",
        "enabled": False,
        "blocks": []        # List of code blocks assigned to this ISR
    }
    
    # Add back the hardware point Timer1_CHC_Comp
    current_dict[prog_name]["software_points"]["Timer1_CHC_Comp"] = {
        "type": "int",
        "default": 0,
        "min_en": False,
        "max_en": False,
        "min": 0,
        "max": 1,
        "hardware": True,
        "int_type": "uint16_t",
        "float_type": "",
        "const": True,
        "_name": "Timer1_CHC_Comp"
    }
    return True

# Clears the current state of the controller to (near) default state so that it can be procedurally allocated (by GUI)
def clear_controller(current_dict, controller_name):

    current_dict[controller_name]["arrays"].clear()                                     # Clear all arrays

    block_lists = code_block_utils.find_lists(current_dict, controller_name)            # Find all block lists
    for block_list in block_lists:                                                      # Clear all block lists
        block_lists[block_list].clear()                                                                  

    for key in current_dict[controller_name]["pin_config"]:                             
        current_dict[controller_name]["pin_config"][key]["enabled"] = False             # Disable all pins
        current_dict[controller_name]["pin_config"][key]["direction"] = "INPUT"         # Set all  pins to default settings
        current_dict[controller_name]["pin_config"][key]["analog_set"] = False
        current_dict[controller_name]["pin_config"][key]["pwm_set"] = False
        current_dict[controller_name]["pin_config"][key]["int_set"] = False

    keys_to_delete = []
    for key in current_dict[controller_name]["software_points"]:                        
        if current_dict[controller_name]["software_points"][key]["hardware"] == False:
            keys_to_delete.append(key)
        else:
            current_dict[controller_name]["software_points"][key]["type"] = "int"       # Reset all hardware points to original values
            current_dict[controller_name]["software_points"][key]["default"] = 1
            #current_dict[controller_name]["software_points"][key]["hold"] = False
            #current_dict[controller_name]["software_points"][key]["hold_val"] = 1
            current_dict[controller_name]["software_points"][key]["min_en"] = False
            current_dict[controller_name]["software_points"][key]["max_en"] = False
            current_dict[controller_name]["software_points"][key]["min"] = 0
            current_dict[controller_name]["software_points"][key]["max"] = 1
            current_dict[controller_name]["software_points"][key]["int_type"] = ""
            current_dict[controller_name]["software_points"][key]["float_type"] = ""
            current_dict[controller_name]["software_points"][key]["const"] = False

    for key in keys_to_delete:
        del current_dict[controller_name]["software_points"][key]

    for key in current_dict[controller_name]["int_config"]:
        current_dict[controller_name]["int_config"][key]["enabled"] = False

    for key in current_dict[controller_name]["timers"]:
        current_dict[controller_name]["timers"][key]["enabled"] = False

    return True