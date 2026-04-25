# create_block_lib.py
# This file creates and initializes the default block library (coding blocks)

# Import Needed Libraries
import pathlib  # Manages file paths and files
import json     # Manages JSON files and writing dictionaries to file
import textwrap # Manages text formatting to remove indents from code blocks

from . import code_block_utils
from . import print_log

# Ensure a copy of the code blocks library exists at run-time
def initialize_block_lib():
    file_path = pathlib.Path("block_lib.json")          # Determine the file path and check for existance
    if file_path.exists():
        return True

    block_lib = {}                                      # Initialize dict object
    block_lib = create_block_lib(block_lib)             # Add all blocks to the library (defined below)

    try:                                                # Attempt to create the file (since it does not exist)
        with open(file_path, 'w') as json_file:
            json.dump(block_lib, json_file, indent=4)
        return True
    
    except Exception as e:                              # Throw an exception if this fails and return false
        print_log.pL("System", "Error", "An unexpected error has occured.", "System", True, {e})
        return False  
    
# Define code blocks and add them to library
def create_block_lib(block_lib):

    ### ARITHMETIC BLOCKS ###

    # Assign Block
    assign_blk = code_block_utils.get_block_type()
    assign_blk["input_points"] = {"left" : "num", "right" : "num"}  # Block Inputs
    assign_blk["output_points"] = {}                                # Block Outputs
    assign_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    assign_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                    # Logical code using [[point]] to represent points
    assign_blk["code_str"] = textwrap.dedent(
    f"""               
    [[left]] = [[right]];
    """)
    assign_blk["description"] = "Performs assignment left = right"
    block_lib["assign_blk"] = assign_blk                            # Store the new block in the block library

    #  Increment Block
    inrement_blk = code_block_utils.get_block_type()
    inrement_blk["input_points"] = {"point" : "num"}                  # Block Inputs
    inrement_blk["output_points"] = {}                                # Block Outputs
    inrement_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    inrement_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                      # Logical code using [[point]] to represent points
    inrement_blk["code_str"] = textwrap.dedent(
    f"""               
    [[point]] += 1;
    """)
    inrement_blk["description"] = "Performs assignment left = right"
    block_lib["inrement_blk"] = inrement_blk                          # Store the new block in the block library




    return block_lib
    