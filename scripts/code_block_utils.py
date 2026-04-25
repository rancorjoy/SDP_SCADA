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

from . import print_log

# This function returns a dictionary of one point, such that inputs/outputs can be modeled
def get_point_list():
    return {
        "point_1": None,
    }


# This function returns a properly formatted empty code block (type)
def get_block_type():
    return {
        "inputs" : get_point_list(),
        "outputs" : get_point_list(),
        "type" : "Input",               # What kind of block is this (categorically)?
        "dep_list" : {},                # Store dependancies in a set so they can be merged later
        "code" : f""                    # This f-string stores the code for this code block, all code blocks will be wrapped as a function with inputs and return outputs
    }

# This function returns an instance of a block which should be added to a block list to be executed in order
def get_block_inst(block_type, inputs, outputs):    # Block type dictionary, either "setup" "loop" or an ISR name, dicts of input points and output points
    return {
        "block_type" : block_type,
        "inputs" : inputs,
        "outputs" : outputs
    }

# Move element closer to top of list by swapping with element above, where index 0 (first) is top of list (first function to run)
def block_list_move_up(block_list, index):
        if index <= 0:
             return False
        if index > 0:
             block_list[index], block_list[index-1] = block_list[index-1], block_list[index]
             return True
        
# Move element closer to bottom of list by swapping with element below, where index n (last) is bottom of list (last function to run)
def block_list_move_up(block_list, index):
        length = len(block_list) - 1
        if index >= length:
             return False
        if index < length:
             block_list[index], block_list[index+1] = block_list[index+1], block_list[index]
             return True
    


