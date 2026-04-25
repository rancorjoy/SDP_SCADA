#code_block_utils.py
# This file contains the methods needed to create and manage code block objects
# Points are software points (dict) as defined in dcs_dict_utils

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON
import textwrap # For dedent (removes tabs in f-strings)

from . import dcs_dict_utils
from . import ino_utils
from . import dcs_script_utils
from . import print_log

# This function returns a properly formatted empty code block (type)
def get_block_type():
    return {
        "input_points"  : {},           # Stores dictionaries of points, {key} : {val} -> {name} : {type}
        "output_points" : {},           # Type can be int, float, bool, num (int or float), any
        "type" : "Input",               # What kind of block is this (categorically)?
        "description" : "",             # Description of the block (what does it do?)
        "dep_list" : [],                # Store dependancies in a list so they can be added together at end
                                        # This f-string stores the code for this code block, all code blocks will be wrapped as a function with inputs and return outputs
        "code_str" : textwrap.dedent(f"""               
        // Logical Code Here
        """)
    }

# This function returns an instance of a block which should be added to a block list to be executed in order
def get_block_inst(block_type):    # Block type dictionary, either "setup" "loop" or an ISR name, dicts of input points and output points
    return {
        "block_type" : block_type,                  # Key in block types dictionary to get block type
        "input_points" : {},                        # Should be key : point where key returns the type in the block_type
        "output_points" : {},
        "condition" : None                          # If this is set to a point (bool), the block will only run if True (adds condition)
    }

# Check if block in library
def block_exist(block_type, block_lib):
    return block_type in block_lib

# Move element closer to top of list by swapping with element above, where index 0 (first) is top of list (first function to run)
def block_list_move_up(curr_dict, controller_name, block_list_str, index):
        
    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False

    block_list = block_lists[block_list_str]

    if index <= 0:
            return False
    if index > 0:
            block_list[index], block_list[index-1] = block_list[index-1], block_list[index]
            return True
        
# Move element closer to bottom of list by swapping with element below, where index n (last) is bottom of list (last function to run)
def block_list_move_down(curr_dict, controller_name, block_list_str, index):

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False

    block_list = block_lists[block_list_str]

    length = len(block_list) - 1
    if index >= length:
            return False
    if index < length:
            block_list[index], block_list[index+1] = block_list[index+1], block_list[index]
            return True

# Swap element positions in a list    
def block_list_swap(curr_dict, controller_name, block_list_str, index_a, index_b):
    length = len(block_list) - 1

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False

    block_list = block_lists[block_list_str]

    if index_a > 0 and index_a < length and index_b > 0 and index_b < length:
        block_list[index_a], block_list[index_b] = block_list[index_b], block_list[index_a]
        return True
    return False

# Add code block to top of list
def add_block_top(curr_dict, controller_name, block_list_str, block_type, block_lib):

    block_lists = find_lists(curr_dict, controller_name)
    
    if block_list_str not in block_lists:
         return False

    if block_exist(block_type, block_lib) == False:
        return False

    block_list = block_lists[block_list_str]

    block_list.insert(0, get_block_inst(block_type))
    return True

# Add code block to bottom of list
def add_block_bot(curr_dict, controller_name, block_list_str, block_type, block_lib):

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False

    if block_exist(block_type, block_lib) == False:
        return False

    block_list = block_lists[block_list_str]

    block_list.append(get_block_inst(block_type))
    return True

# Add code block to index n of list
def add_block_index(curr_dict, controller_name, block_list_str, block_type, index, block_lib):

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False
    
    if index >= len(block_list):
        return False
    
    if block_exist(block_type, block_lib) == False:
        return False

    block_list = block_lists[block_list_str]

    block_list.insert(index, get_block_inst(block_type))
    return True

# Remove code block at index n of list
def remove_block_index(curr_dict, controller_name, block_list_str, index): 

    if index >= len(block_list):
        return False

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return False
    
    block_list = block_lists[block_list_str]

    block_list.pop(index)
    return True

# Discover which block lists exist for a controller - delete the obsolete ones
def find_lists(curr_dict, controller_name):
      
    # Setup and loop blocks are at known locations and never get disabled
    found_lists = {"setup_blocks": curr_dict[controller_name]["setup_blocks"], "loop_blocks" : curr_dict[controller_name]["loop_blocks"]}

    for key in curr_dict[controller_name]["int_config"]:
        if curr_dict[controller_name]["int_config"][key]["enabled"] == False:
            curr_dict[controller_name]["int_config"][key]["blocks"].clear() # If the interrupt is disabled, delete the list to prevent code errors!
            
        else:                                                                   # Logic for enabled interrupts
            if key.startswith("DP"):
                if curr_dict[controller_name]["software_points"][key]["enabled"]:
                    found_lists[key] = curr_dict[controller_name]["int_config"][key]["blocks"]
                else:
                    curr_dict[controller_name]["int_config"][key]["blocks"].clear()     # If the interrupt is enabled somehow, delete the list to prevent code errors!
                    curr_dict[controller_name]["int_config"][key]["enabled"] = False    # This should be true already but this condition means it was not set!
                
            else:                                                                       # Thus this interrupt is a timer interrupt that is enabled -> it must have a list
                found_lists[key] = curr_dict[controller_name]["int_config"][key]["blocks"]
    return found_lists

# Function to get block_inst from Flask command (middle-man function)
def get_inst(curr_dict, controller_name, block_list_str, index):

    block_lists = find_lists(curr_dict, controller_name)
    if block_list_str not in block_lists:
         return None

    block_list = block_lists[block_list_str]

    if index >= len(block_list) or index < 0:
        return None    
    
    return block_list[index]

# Add point to input of block
def add_point_input(block_inst, var_name, point):
     
    if block_inst == None:
        return False

    if block_inst["input_points"][var_name]:                            # The variable is already assigned!
          return False
     
    required_type = []                                                  # Get a list of possible types the function can accept for this point/variable
    if block_inst["block_type"]["input_points"][var_name] == "bool":
        required_type = ["bool"]
    elif block_inst["block_type"]["input_points"][var_name] == "int":
         required_type = ["int"]
    elif block_inst["block_type"]["input_points"][var_name] == "float":
         required_type = ["float"]
    elif block_inst["block_type"]["input_points"][var_name] == "num":
         required_type = ["float", "int"]
    elif block_inst["block_type"]["input_points"][var_name] == "any":
         required_type = ["float", "int", "bool"]

    if point["type"] not in required_type:                              # The point is none of the needed types
        return False
    
    block_inst["input_points"][var_name] = point                        # Correct variable and empty spot -> assigned!

# Add point to output of block
def add_point_output(block_inst, var_name, point):

    if block_inst == None:
        return False
     
    if block_inst["output_points"][var_name]:                            # The variable is already assigned!
          return False
     
    required_type = []                                                  # Get a list of possible types the function can accept for this point/variable
    if block_inst["block_type"]["output_points"][var_name] == "bool":
        required_type = ["bool"]
    elif block_inst["block_type"]["output_points"][var_name] == "int":
         required_type = ["int"]
    elif block_inst["block_type"]["output_points"][var_name] == "float":
         required_type = ["float"]
    elif block_inst["block_type"]["output_points"][var_name] == "num":
         required_type = ["float", "int"]
    elif block_inst["block_type"]["output_points"][var_name] == "any":
         required_type = ["float", "int", "bool"]

    if point["type"] not in required_type:                              # The point is none of the needed types
        return False
    
    block_inst["output_points"][var_name] = point                       # Correct variable and empty spot -> assigned!
    return True

# Remove point from input position
def remove_point_input(block_inst, var_name):
    if block_inst["input_points"][var_name]:                            # Check it exists first
         del block_inst["input_points"][var_name]                       # Delete it
         return True
    return False

# Remove point from output position
def remove_point_output(block_inst, var_name):
    if block_inst["output_points"][var_name]:                           # Check it exists first
         del block_inst["output_points"][var_name]                      # Delete it
         return True
    return False

# List block details and definitions
def display_block_details(blk_type_name, block_type):
    struc_str = f"{blk_type_name}"
    for key in block_type["input_points"]:
        struc_str += f" <{key}>"
    struc_str += f" :"
    for key in block_type["output_points"]:
        struc_str += f" <{key}>"
    struc_str += f"\n"

    des_str = f"{blk_type_name} : {block_type['description']}\n\n"
    return struc_str + des_str

# List a listing of all known block types
def display_block_help(block_lib):
    block_cats = []
    for blk_type_name in block_lib:
        if block_lib[blk_type_name]["type"] not in block_cats:
            block_cats.append(block_lib[blk_type_name]["type"])

    ret_str = ""
    for this_type in block_cats:
        ret_str += f"{this_type} Blocks:\n\n"
        for blk_type_name in block_lib:
            if block_lib[blk_type_name]["type"] == this_type:
                ret_str += display_block_details(blk_type_name, block_lib[blk_type_name])

    ret_str += "\n"
    return ret_str

# List a detailed and neat readout of the current configuration to assist the user (current state)
def display_current_config(curr_dict, controller_name, block_lib):
    block_lists = find_lists(curr_dict, controller_name)

    block_types_used = []
    for list_key in block_lists:
        for blk_inst in block_lists[list_key]:
            if blk_inst["block_type"] not in block_types_used:
                block_types_used.append(blk_inst["block_type"])

    ret_str = f"Block Types Used:\n\n"
    for blk_type_name in block_types_used:
        ret_str += display_block_details(blk_type_name, block_lib[blk_type_name])

    for this_list in block_lists:
        ret_str += f"\n{this_list}:\n"
        for blk_inst in block_lists[this_list]:
            blk_type = block_lib[blk_inst["block_type"]]
            struc_str = f"{blk_inst['block_type']}"  # use the name string, not the dict
            for key in blk_type["input_points"]:
                val = blk_inst["input_points"].get(key, "")
                struc_str += f" <{val}>"
            struc_str += " :"
            for key in blk_type["output_points"]:
                val = blk_inst["output_points"].get(key, "")
                struc_str += f" <{val}>"
            struc_str += "\n"
            ret_str += struc_str

    return ret_str

# List all available lists in a controller
def display_lists(curr_dict, controller_name):
     
    block_lists = find_lists(curr_dict, controller_name)

    ret_str = f"{controller_name} Block Lists:\n"
    for key in block_lists:
        ret_str += f"{key}\n"

    ret_str += f"\n"
    return ret_str
              
# List a detailed and neat readout of the current configuration to assist the user (saved state)
def display_saved_config(data_path, controller_name, block_lib):
    cont = dcs_dict_utils.get_dict(data_path, controller_name)
    curr_dict = {controller_name: cont}
    block_lists = find_lists(curr_dict, controller_name)

    block_types_used = []
    for list_key in block_lists:
        for blk_inst in block_lists[list_key]:
            if blk_inst["block_type"] not in block_types_used:
                block_types_used.append(blk_inst["block_type"])

    ret_str = f"Block Types Used:\n\n"
    for blk_type_name in block_types_used:
        ret_str += display_block_details(blk_type_name, block_lib[blk_type_name])

    for this_list in block_lists:
        struc_str = ""
        ret_str += f"\n{this_list}:\n"
        for blk_inst in block_lists[this_list]:
            blk_type = block_lib[blk_inst["block_type"]]
            struc_str = f"{blk_inst['block_type']}"
            for key in blk_type["input_points"]:
                val = blk_inst["input_points"].get(key, "")
                struc_str += f" <{val}>"
            struc_str += " :"
            for key in blk_type["output_points"]:
                val = blk_inst["output_points"].get(key, "")
                struc_str += f" <{val}>"
            struc_str += "\n"
            ret_str += struc_str

    return ret_str

# Validate that the "code" saved has no obvious errors and log warnings:
def validate_config(data_path, controller_name):
    warnings = []
    errors = []

    # Validation checks add errors and warnings, warnings are shown but ignored
    # Warnings and errors are lists [] NOT dicts []

    warnings.append(f"Test Warning")
    errors.append(f"Test Error")

    return {"warnings" : warnings, "errors" : errors}   # Return warnings and errors

# Gets boolean result of validation  - only compile if true!
def valid_to_bool(valid):
    if len(valid["errors"]) == 0:
        return True
    return False

# Show validation as ret_str
def print_validation(data_path, controller_name, block_lib): 
    ret_str = display_saved_config(data_path, controller_name, block_lib)
    ret_str += "\n"

    valid = validate_config(data_path, controller_name)

    if len(valid["warnings"]) != 0:
        ret_str += "Warnings:\n"
        for warn in valid["warnings"]:
            ret_str += warn
            ret_str += f"\n"

    if len(valid["errors"]) != 0:
        ret_str += "\n\nErrors:\n"
        for err in valid["errors"]:
            ret_str += err
            ret_str += f"\n"

    return ret_str

# if cmd == "compile_dcs":    return {"ok": True, "result": dcs_script_utils.create_Script(get_path(), args[0], ino_utils.get_code(get_path(), args[0]))}

# Compile pipeline with validation
def check_compile(data_path, controller_name):

    valid = valid_to_bool(validate_config(data_path, controller_name))

    if valid:
        return dcs_script_utils.create_Script(data_path, controller_name, ino_utils.get_code(data_path, controller_name))
    
    return False