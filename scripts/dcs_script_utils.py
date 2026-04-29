# dcs_script_utils.py
# This file contains the methods needed to create, rename, delete, etc ino scripts in the file system

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

from . import dcs_dict_utils
from . import print_log

# Function to create an ino script for a controller
def create_Script(data_path, name, code_str):

    data_path = pathlib.Path(data_path)                              # Ensure data path is a path (works for path and string inputs)
    script_path = data_path / pathlib.Path("dcs_scripts") / name     # Assign dcs_path to data_path/dcs_info (name of folder)

    saved_dict = dcs_dict_utils.get_dict(data_path, name)            # Ensures a script cannot be made for an empty (code) controller
    if dcs_dict_utils.is_prog(saved_dict):
        return False
    
    folder_made = False                                              # Keeps track of whether the folder has been made

    try:
        script_path.mkdir(parents=True, exist_ok=True)
        folder_made = True
        
    except FileExistsError:
        return False
    except PermissionError:
        print_log.pL("System", "Error", f"Permission denied when creating script folder {name}.", "System", True, None)
        return False
    except OSError as e:
        print_log.pL("System", "Error", f"An unexpected error has occured.", "System", True, {e})
        return False

    # If that worked, attempt to make an ino file - this could be done in same try catch but I wanted to separate them for error logging purposes :)
    if folder_made:
        try:
            pathlib.Path(script_path / f"{name}.ino").write_text(code_str)
            return True
        except PermissionError:
            print_log.pL("System", "Error", f"Permission denied when creating ino sctipt {name}", "System", True, None)
            return False
        except OSError as e:
            print_log.pL("System", "Error", f"An unexpected error has occured.", "System", True, {e})
            return False


# Function to rename an ino script for a controller
def rename_Script(data_path, old_name, new_name):
    data_path = pathlib.Path(data_path)
    script_path = data_path / "dcs_scripts" / old_name
    new_path = data_path / "dcs_scripts" / new_name

    if not script_path.exists():
        print_log.pL("System", "Error", f"Script folder {old_name} not found.", "System", True, None)
        return False

    if new_path.exists():
        print_log.pL("System", "Error", f"Script folder {new_name} already exists.", "System", True, None)
        return False

    try:
        # Rename folder first
        script_path.rename(new_path)

        # Then rename ino file inside
        old_ino = new_path / f"{old_name}.ino"
        new_ino = new_path / f"{new_name}.ino"

        if old_ino.exists():
            old_ino.rename(new_ino)

        return True

    except Exception as e:
        print_log.pL("System", "Error", "An unexpected error occurred.", "System", True, {e})
        return False

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