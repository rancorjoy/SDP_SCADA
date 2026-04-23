# dcs_script_utils.py
# This file contains the methods needed to create, rename, delete, etc ino scripts in the file system

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

from . import print_log

# Function to create an ino script for a controller
def create_Script(data_path, name):
    data_path = pathlib.Path(data_path)                              # Ensure data path is a path (works for path and string inputs)
    script_path = data_path / pathlib.Path("dcs_scripts") / name     # Assign dcs_path to data_path/dcs_info (name of folder)
    
    folder_made = False                                              # Keeps track of whether the folder has been made

    try:
        script_path.mkdir(parents=True, exist_ok=False)
        folder_made = True
        
    except FileExistsError:
        # print_log.pL("System", "Error", f"The script folder {name} already exists.", "System", True, None)
        return # This prevents the already exists error from appearing when this is used in the rename script :)
    except PermissionError:
        print_log.pL("System", "Error", f"Permission denied when creating script folder {name}.", "System", True, None)
    except OSError as e:
        print_log.pL("System", "Error", f"An unexpected error has occured.", "System", True, {e})

    # If that worked, attempt to make an ino file - this could be done in same try catch but I wanted to separate them for error logging purposes :)
    if folder_made:
        def_code = f"""
            void setup() {{
            // put your setup code here, to run once:
            }}

            void loop() {{
            // put your main code here, to run repeatedly:
            }}
            """
        try:
            pathlib.Path(script_path / f"{name}.ino").write_text(def_code)
        except PermissionError:
            print_log.pL("System", "Error", f"Permission denied when creating ino sctipt {name}", "System", True, None)
        except OSError as e:
            print_log.pL("System", "Error", f"An unexpected error has occured.", "System", True, {e})


# Function to rename an ino script for a controller
def rename_Script(data_path, old_name, new_name):
    data_path = pathlib.Path(data_path)                                 # Ensure data path is a path (works for path and string inputs)
    script_path = data_path / pathlib.Path("dcs_scripts") / old_name    # Assign dcs_path to data_path/dcs_info (name of folder)
    new_path = data_path / pathlib.Path("dcs_scripts") / new_name    

    renamed = False                                                     # Keeps track of whether ino has been renamed

    try:
        pathlib.Path(script_path / f"{old_name}.ino").rename(pathlib.Path(script_path / f"{new_name}.ino"))
        renamed = True

    # Attempt to rename the ino file
    except FileNotFoundError:
        print_log.pL("System", "Error", f"DCS ino file {old_name} not found.", "System", True, None)
    except PermissionError:
        print_log.pL("System", "Error", f"Permission denied for {old_name} ino file.", "System", True, None)
    except Exception as e:
        print_log.pL("System", "Error", f"An unexpected error occurred.", "System", True, {e})

    # If that worked, attempt to rename folder - this could be done in same try catch but I wanted to separate them for error logging purposes :)
    if renamed:
        try:
            script_path.rename(new_path)
    
        except FileNotFoundError:
            print_log.pL("System", "Error", f"Script folder {old_name} not found.", "System", True, None)
        except OSError as e:
            print_log.pL("System", "Error", f"An unexpected error occurred.", "System", True, {e})

# Function to remove an ino script for a controller
def remove_Script(data_path, name):
    data_path = pathlib.Path(data_path)                              # Ensure data path is a path (works for path and string inputs)
    script_path = data_path / pathlib.Path("dcs_scripts") / name     # Assign dcs_path to data_path/dcs_info (name of folder)
    
    try:
        (script_path / f"{name}.ino").unlink()
        script_path.rmdir()

    except FileNotFoundError:
        print_log.pL("System", "Error", f"The script folder {name} does not exist.", "System", True, None)
    except OSError as e:
        # rmdir raises OSError if the directory is not empty
        print_log.pL("System", "Error", f"Cannot delete script folder {name} does not exist.", "System", True, {e})
    except Exception as e:
        print_log.pL("System", "Error", f"An unexpected error occurred.", "System", True, {e})