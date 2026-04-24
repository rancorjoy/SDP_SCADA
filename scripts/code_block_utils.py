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

# This function returns a list of dependancies, will be added to total dependancy list when all code blocks are loaded
def get_dep_list():
    return {
        "dep_1": None,
    }

# This function returns a properly formatted empty code block (type)
def get_block_type(name):
    return {
        "name": name,
        "inputs" : get_point_list(),
        "outputs" : get_point_list(),
        "type" : "Input",               # What kind of block is this (categorically)?
        "dep_list" : get_dep_list,      # This stores the dependancies for this code block type
        "code" : f""                    # This f-string stores the code for this code block, all code blocks will be wrapped as a function with inputs and return outputs
    }

# This function returns an instance of a block which should be added to a block list to be executed in order
def get_block_inst(block_type, position, inputs, outputs):    # Block type dictionary, either "setup" "loop" or an ISR name, dicts of input points and output points
    return {
        "block_type" : block_type,
        "inputs" : inputs,
        "outputs" : outputs
    }


