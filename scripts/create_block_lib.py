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

# Open a copy of the library to save in the current state at run time
def open_block_lib():
    file_path = pathlib.Path("block_lib.json")          # Determine the file path and check for existance
    
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)
    
    return None

# Define code blocks and add them to library
def create_block_lib(block_lib):

    ### ARITHMETIC BLOCKS ###

    # Assign Block
    assign_blk = code_block_utils.get_block_type()
    assign_blk["input_points"] = {"right" : "num"}                  # Block Inputs
    assign_blk["output_points"] = {"left" : "num"}                  # Block Outputs
    assign_blk["output_type_case"] = {"left" : "decltype(right_t())"}
    assign_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    assign_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                    # Logical code using point to represent points
    assign_blk["code_str"] = textwrap.dedent(
    """               
    left = right;
    """)
    assign_blk["description"] = "Performs assignment left = right."
    block_lib["assign_blk"] = assign_blk                            # Store the new block in the block library

    # Bool Assign Block
    assign_blk = code_block_utils.get_block_type()
    assign_blk["input_points"] = {"right" : "bool"}                  # Block Inputs
    assign_blk["output_points"] = {"left" : "bool"}                 # Block Outputs
    assign_blk["output_type_case"] = {"left" : "bool"}
    assign_blk["type"] = "Logical"                                  # Meta-Data to help with organizing
    assign_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                    # Logical code using point to represent points
    assign_blk["code_str"] = textwrap.dedent(
    """               
    left = right;
    """)
    assign_blk["description"] = "Performs assignment left = right for booleans."
    block_lib["bool_assign_blk"] = assign_blk                            # Store the new block in the block library

    #  Increment Block
    increment_blk = code_block_utils.get_block_type()
    increment_blk["input_points"] = {"point" : "num"}                  # Block Inputs
    increment_blk["output_points"] = {"point_out" : "num"}                 # Block Outputs
    increment_blk["output_type_case"] = {"point_out" : "decltype(point_t())"}
    increment_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    increment_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                       # Logical code using point to represent points
    increment_blk["code_str"] = textwrap.dedent(
    """               
    point_out = point + 1;
    """)
    increment_blk["description"] = "Increments the value of point by 1."
    block_lib["increment_blk"] = increment_blk                          # Store the new block in the block library

    #  Decrement Block
    decrement_blk = code_block_utils.get_block_type()
    decrement_blk["input_points"] = {"point" : "num"}                  # Block Inputs
    decrement_blk["output_points"] = {}                                # Block Outputs
    decrement_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    decrement_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                        # Logical code using point to represent points
    decrement_blk["code_str"] = textwrap.dedent(
    """               
    point -= 1;
    """)
    decrement_blk["description"] = "Decrements the value of point by 1."
    block_lib["decrement_blk"] = decrement_blk                          # Store the new block in the block library

    #  Addition Block
    add_blk = code_block_utils.get_block_type()
    add_blk["input_points"] = {"add1" : "num", "add2" : "num"}   # Block Inputs
    add_blk["output_points"] = {"sum" : "num"}                   # Block Outputs
    add_blk["output_type_case"] = {"sum" : "decltype(add1_t() + add2_t())"}
    add_blk["type"] = "Arithmetic"                               # Meta-Data to help with organizing
    add_blk["dep_list"] = []                                     # List of dependancies saved as strings
                                                                 # Logical code using point to represent points
    add_blk["code_str"] = textwrap.dedent(
    """               
    sum = add1 + add2;
    """)
    add_blk["description"] = "Adds add1 + add2 and returns sum."
    block_lib["add_blk"] = add_blk                              # Store the new block in the block library

    #  Subtraction Block
    sub_blk = code_block_utils.get_block_type()
    sub_blk["input_points"] = {"minuend" : "num", "subtrahend" : "num"}     # Block Inputs
    sub_blk["output_points"] = {"difference" : "num"}                       # Block Outputs
    sub_blk["output_type_case"] = {"difference" : "decltype(minuend_t() - subtrahend_t())"}
    sub_blk["type"] = "Arithmetic"                                          # Meta-Data to help with organizing
    sub_blk["dep_list"] = []                                                # List of dependancies saved as strings
                                                                            # Logical code using point to represent points
    sub_blk["code_str"] = textwrap.dedent(
    """               
    difference = minuend - subtrahend;
    """)
    sub_blk["description"] = "Subtracts minuend - subtrahend and returns difference."
    block_lib["sub_blk"] = sub_blk                                          # Store the new block in the block library

    #  Multiplication Block
    mul_blk = code_block_utils.get_block_type()
    mul_blk["input_points"] = {"factor1" : "num", "factor2" : "num"}    # Block Inputs
    mul_blk["output_points"] = {"product" : "num"}                      # Block Outputs
    mul_blk["output_type_case"] = {"product" : "decltype(factor1_t() * factor2_t())"}
    mul_blk["type"] = "Arithmetic"                                      # Meta-Data to help with organizing
    mul_blk["dep_list"] = []                                            # List of dependancies saved as strings
                                                                        # Logical code using point to represent points
    mul_blk["code_str"] = textwrap.dedent(
    """               
    product = factor1 * factor2;
    """)
    mul_blk["description"] = "Multiplies factor1 * factor2 and returns product."
    block_lib["mul_blk"] = mul_blk                                      # Store the new block in the block library

    #  Division Block
    div_blk = code_block_utils.get_block_type()
    div_blk["input_points"] = {"dividend" : "num", "divisor" : "num"}   # Block Inputs
    div_blk["output_points"] = {"quotient" : "num"}                     # Block Outputs
    div_blk["output_type_case"] = {"quotient" : "decltype(dividend_t() / divisor_t())"}
    div_blk["type"] = "Arithmetic"                                      # Meta-Data to help with organizing
    div_blk["dep_list"] = []                                            # List of dependancies saved as strings
                                                                        # Logical code using point to represent points
    div_blk["code_str"] = textwrap.dedent(
    """               
    quotient = dividend / divisor;
    """)
    div_blk["description"] = "Divides dividend / divisor and returns quotient."
    block_lib["div_blk"] = div_blk                                      # Store the new block in the block library

    #  Euclidean Division Block
    ediv_blk = code_block_utils.get_block_type()
    ediv_blk["input_points"] = {"dividend" : "int", "divisor" : "int"}       # Block Inputs
    ediv_blk["output_points"] = {"quotient" : "int", "remainder" : "int"}    # Block Outputs
    ediv_blk["output_type_case"] = {"quotient" : "decltype(dividend_t() / divisor_t())", "remainder" : f"decltype(dividend_t() % divisor_t())"}
    ediv_blk["type"] = "Arithmetic"                                          # Meta-Data to help with organizing
    ediv_blk["dep_list"] = []                                                # List of dependancies saved as strings
                                                                             # Logical code using point to represent points
    ediv_blk["code_str"] = textwrap.dedent(
    """               
    if (divisor == 0) {{
        quotient = 0;
        remainder = dividend;  // preserves a = bq + r
    }} 
    else {{
        remainder = dividend % divisor;
        if (remainder < 0) {{
            remainder += abs(divisor);
        }}
        quotient = (dividend - remainder) / divisor;
    }}
    """)
    ediv_blk["description"] = "Divides (Euclidean) dividend / divisor and returns quotient and remainder."
    block_lib["ediv_blk"] = ediv_blk                                          # Store the new block in the block library



    ### ARRAY BLOCKS ###
    
    new_blk = code_block_utils.get_block_type()
    new_blk["input_points"] = {"reading" : "num", "index" : "int", "length" : "int", "arr" : "arr"}  # Block Inputs
    new_blk["output_points"] = {"index_out" : "int", "avg" : "float"}                        # Block Outputs
    new_blk["output_type_case"] = {"index_out" : "int", "avg" : "float"}
    new_blk["type"] = "Array"                                             # Meta-Data to help with organizing
    new_blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                          # Logical code using point to represent points
    new_blk["code_str"] = textwrap.dedent(
    """               
    index_out = index + 1;
    if(index_out == length) { index_out = 0; }
    arr[index_out] = reading;

    float sum = 0;
    for (int i=0; i<length; i++)
    {
        sum += (float)arr[i];
    }
    avg = sum/length;
    """)
    new_blk["description"] = "Takes the moving average of an array of length and returns the average."
    block_lib["moving_avg_blk"] = new_blk                                      # Store the new block in the block library


    ### LOGICAL BLOCKS ###

    # Equivelence
    equal_blk = code_block_utils.get_block_type()
    equal_blk["input_points"] = {"argument1" : "any", "argument2" : "any"}  # Block Inputs
    equal_blk["output_points"] = {"result" : "bool"}                        # Block Outputs
    equal_blk["output_type_case"] = {"result" : "bool"}
    equal_blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    equal_blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                            # Logical code using point to represent points
    equal_blk["code_str"] = textwrap.dedent(
    """               
    argument1 == argument2 ? result = true : result = false;
    """)
    equal_blk["description"] = "Checks if argument1 and argument2 are equal and returns result."
    block_lib["equal_blk"] = equal_blk                                      # Store the new block in the block library

    # Greater Than
    greater_blk = code_block_utils.get_block_type()
    greater_blk["input_points"] = {"argument1" : "any", "argument2" : "any"}    # Block Inputs
    greater_blk["output_points"] = {"result" : "bool"}                          # Block Outputs
    greater_blk["output_type_case"] = {"result" : "bool"}
    greater_blk["type"] = "Logical"                                             # Meta-Data to help with organizing
    greater_blk["dep_list"] = []                                                # List of dependancies saved as strings
                                                                                # Logical code using point to represent points
    greater_blk["code_str"] = textwrap.dedent(
    """               
    argument1 > argument2 ? result = true : result = false;
    """)
    greater_blk["description"] = "Checks if argument1 > argument2 are equal and returns result."
    block_lib["greater_blk"] = greater_blk                                      # Store the new block in the block library

    # Greater Than or Equal
    greater_equal_blk = code_block_utils.get_block_type()
    greater_equal_blk["input_points"] = {"argument1" : "any", "argument2" : "any"}  # Block Inputs
    greater_equal_blk["output_points"] = {"result" : "bool"}                        # Block Outputs
    greater_equal_blk["output_type_case"] = {"result" : "bool"}
    greater_equal_blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    greater_equal_blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                                    # Logical code using point to represent points
    greater_equal_blk["code_str"] = textwrap.dedent(
    """               
    argument1 >= argument2 ? result = true : result = false;
    """)
    greater_equal_blk["description"] = "Checks if argument1 >= argument2 are equal and returns result."
    block_lib["greater_equal_blk"] = greater_equal_blk                              # Store the new block in the block library

    # Lesser Than
    lesser_blk = code_block_utils.get_block_type()
    lesser_blk["input_points"] = {"argument1" : "any", "argument2" : "any"}    # Block Inputs
    lesser_blk["output_points"] = {"result" : "bool"}                          # Block Outputs
    lesser_blk["output_type_case"] = {"result" : "bool"}
    lesser_blk["type"] = "Logical"                                             # Meta-Data to help with organizing
    lesser_blk["dep_list"] = []                                                # List of dependancies saved as strings
                                                                                # Logical code using point to represent points
    lesser_blk["code_str"] = textwrap.dedent(
    """               
    argument1 < argument2 ? result = true : result = false;
    """)
    lesser_blk["description"] = "Checks if argument1 < argument2 are equal and returns result."
    block_lib["lesser_blk"] = lesser_blk                                      # Store the new block in the block library

    # Lesser Than or Equal
    lesser_equal_blk = code_block_utils.get_block_type()
    lesser_equal_blk["input_points"] = {"argument1" : "any", "argument2" : "any"}  # Block Inputs
    lesser_equal_blk["output_points"] = {"result" : "bool"}                        # Block Outputs
    lesser_equal_blk["output_type_case"] = {"result" : "bool"}
    lesser_equal_blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    lesser_equal_blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                                    # Logical code using point to represent points
    lesser_equal_blk["code_str"] = textwrap.dedent(
    """               
    argument1 <= argument2 ? result = true : result = false;
    """)
    lesser_equal_blk["description"] = "Checks if argument1 =< argument2 are equal and returns result."
    block_lib["lesser_equal_blk"] = lesser_equal_blk                              # Store the new block in the block library

    # Invert Self
    blk = code_block_utils.get_block_type()
    blk["input_points"] = {"argument1" : "bool"}                      # Block Inputs
    blk["output_points"] = {}                                         # Block Outputs
    blk["output_type_case"] = {}
    blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                      # Logical code using point to represent points
    blk["code_str"] = textwrap.dedent(
    """               
    argument1 == true ? argument1 = false : argument1 = true;
    """)
    blk["description"] = "Inverts the given argument1."
    block_lib["inv_self_blk"] = blk                                 # Store the new block in the block library

    # Invert
    blk = code_block_utils.get_block_type()
    blk["input_points"] = {"argument1" : "bool"}                      # Block Inputs
    blk["output_points"] = {"result" : "bool"}                        # Block Outputs
    blk["output_type_case"] = {"result" : "bool"}
    blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                      # Logical code using point to represent points
    blk["code_str"] = textwrap.dedent(
    """               
    argument1 == true ? result = false : result = true;
    """)
    blk["description"] = "result is NOT agument1."
    block_lib["inv_blk"] = blk                                 # Store the new block in the block library

    # OR
    blk = code_block_utils.get_block_type()
    blk["input_points"] = {"argument1" : "bool","argument2" : "bool"}   # Block Inputs
    blk["output_points"] = {"result" : "bool"}                          # Block Outputs
    blk["output_type_case"] = {"result" : "bool"}
    blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                      # Logical code using point to represent points
    blk["code_str"] = textwrap.dedent(
    """               
    argument1 || argument2 ? result = true : result = false;
    """)
    blk["description"] = "OR operation of argument1 OR argument2, returns result."
    block_lib["or_blk"] = blk                                 # Store the new block in the block library

    # AND
    blk = code_block_utils.get_block_type()
    blk["input_points"] = {"argument1" : "bool","argument2" : "bool"}   # Block Inputs
    blk["output_points"] = {"result" : "bool"}                          # Block Outputs
    blk["output_type_case"] = {"result" : "bool"}
    blk["type"] = "Logical"                                           # Meta-Data to help with organizing
    blk["dep_list"] = []                                              # List of dependancies saved as strings
                                                                      # Logical code using point to represent points
    blk["code_str"] = textwrap.dedent(
    """               
    argument1 && argument2 ? result = true : result = false;
    """)
    blk["description"] = "AND operation of argument1 AND argument2, returns result."
    block_lib["and_blk"] = blk                                 # Store the new block in the block library




    return block_lib
    