# data_path_utils.py
# Manages initialization, migration, recovery and path return for the persistent data path

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables

# Persistent Data File Location
_scriptDir = pathlib.Path(__file__).parent                  # Path relative to main SCADA.py file
def_dataPath = _scriptDir.parent.parent / "SCADA_Data"      # Defualt Data Path
man_dataPath = def_dataPath                                 # Manual Data Path <- Default Data Path (Unless changed)
man_pointer = def_dataPath / pathlib.Path("Pointer.json")   # If the manual path is migrated, a pointer JSON will be left behind
                                                            # JSON should contain one field: "man_pointer" with relative data path

# Initiate Data Path
def init_data_path():

    global man_dataPath                                                 # Pass by reference global variable into function
    
    try:                                                                # Try to open and load pointer file to recover manual data path
        with open(man_pointer, 'r') as pointer_file:                    # Attempt to open the pointer JSON file as pointer_file
            json_pointer = json.load(pointer_file)                      # Load the pointer JSON file into json_pointer

        if "man_pointer" in json_pointer:                                   # If the JSON file contains the required field (it should if not tampered with)...
            man_dataPath = pathlib.Path(json_pointer['man_pointer'])        # Set the manual file path to the pointed path
            if man_dataPath != def_dataPath:                                # If the data path is not the default data path, ensure there is a data directory
                try:                                                        # Create a data path if there is not one present  
                    os.makedirs(man_dataPath, exist_ok=True)                # Creates persistent data path if it doesn't already exist
                except PermissionError as e:                                # Failed to create default data path due to folder permissions! - Data cannot be stored!    
                    print(f"Error: Could not create data directory. Check folder permissions.\n  Details: {e}")
                    return False                                            # Failed to resolve data location

                except OSError as e:                                        # Failed to create default data path due to unknown error! - Data cannot be stored!    
                    print(f"Error: Unexpected OS error while creating data directory.\n  Details: {e}")
                    return False                                            # Failed to resolve data location

        else:                                                           # Pointer file exists, manual path lost: store data here              
            print("Warning: Pointer.json missing 'man_pointer' field. Falling back to default path.")
            man_dataPath = def_dataPath                                 # Ensure data path is set to default path
            man_pointer.unlink()                                        # Delete malformed JSON pointer file

    except FileNotFoundError:                                           # Pointer file doesn't exist, data lives at the default path (default state)
        try:                                                            # Create a default data path if there is not one present  
            os.makedirs(def_dataPath, exist_ok=True)                    # Creates persistent data path if it doesn't already exist
        except PermissionError as e:                                    # Failed to create default data path due to folder permissions! - Data cannot be stored!    
            print(f"Error: Could not create data directory. Check folder permissions.\n  Details: {e}")
            return False                                                # Failed to resolve data location

        except OSError as e:                                            # Failed to create default data path due to unknown error! - Data cannot be stored!    
            print(f"Error: Unexpected OS error while creating data directory.\n  Details: {e}")
            return False                                                # Failed to resolve data location

    except json.JSONDecodeError as e:                                   # Pointer file exists but contains malformed/corrupted JSON
        print(f"Warning: Pointer.json is corrupted and could not be read. Falling back to default path.\n  Details: {e}")
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path
        man_pointer.unlink()                                            # Delete malformed JSON pointer file

    except PermissionError as e:                                        # Pointer file exists but cannot be read (permission issue)
        print(f"Error: Could not read Pointer.json, check file permissions. Falling back to default path. \n  Details: {e}")
        man_dataPath = def_dataPath                                     # Ensure data path is set to default path
        try:                                                            # Try to delete malformed JSON pointer file
            man_pointer.unlink()                                        # Delete malformed JSON pointer file
        except OSError:                                                 # If an OS error occurs...
            pass                                                        # Not much we can do, move on :(

    return True                                                         # Data path has been resolved

# Migrate Data Path to Updated Path
def migrate(new_location):
    new_location = (_scriptDir.parent / pathlib.Path(new_location)).resolve()   # Convert provided file path into Path object
    global man_dataPath                                                         # Pass man_dataPath by reference into method

    if new_location == def_dataPath:                                            # If the new location is the default file location ("moving back")
        
        # 1. Copy Old Data Folder Over New Path
        try:                                                                    # Try writing old data path over new data path
            shutil.copytree(man_dataPath, def_dataPath, dirs_exist_ok=True)     # Copy the entire directory tree, overwriting existing files/directories
            print(f"Data Path moved from '{man_dataPath}' to '{def_dataPath}' with overwrite.")
        except FileExistsError as e:                                            # Incase flag dirs_exist_ok=True is ignored or superseded
            print(f"Error: Destination folder already exists and an issue occurred: {e}")
            return False                                                        # The data directory was NOT migrated
        except OSError as e:                                                    # Incase of other OS error
            print(f"Error: {e}")
            return False                                                        # The data directory was NOT migrated

        # 2. Delete the JSON File left in the Default Data Path
        try:                                                                    # Try to delete the JSON file
            man_pointer.unlink()                                                # JSON file unlinked from data tree
            print(f"JSON file '{man_pointer}' has been deleted successfully.")
        except FileNotFoundError:                                               # If the file is missing (somehow?)
            print(f"File '{man_pointer}' does not exist.")                   

        print(f"About to delete: {man_dataPath}")
        print(f"def_dataPath is: {def_dataPath}")

        # 3. Delete Old Data Path
        try:                                                                    # Try deleting the old data path file tree
            shutil.rmtree(man_dataPath)                                         # Delete file tree at man_dataPath
            print(f"Data Path at '{man_dataPath}' deleted successfully.")
        except FileNotFoundError:                                               # Incase the file tree is missing (somehow?)
            print(f"Error: The directory '{man_dataPath}' does not exist.")
            return False                                                        # The data directory was NOT migrated
        except OSError as e:                                                    # Incase of other OS error
            print(f"Error: {e}.")
            return False                                                        # The data directory was NOT migrated

        # 4. Finishing Steps
        man_dataPath = def_dataPath                                             # Reset man_DataPath to def_dataPath value
        return True                                                             # The data directory was migrated


    else:                                                                       # If the new location is NOT the default file location ("moving out")
        
        # 1. Copy Old Data Folder Over New Path
        try:                                                                    # Try writing old data path over new data path
            shutil.copytree(man_dataPath, new_location, dirs_exist_ok=True)     # Copy the entire directory tree, overwriting existing files/directories
            print(f"Data Path moved from '{man_dataPath}' to '{new_location}' with overwrite.")
        except FileExistsError as e:                                            # Incase flag dirs_exist_ok=True is ignored or superseded
            print(f"Error: Destination folder already exists and an issue occurred: {e}")
            return False                                                        # The data directory was NOT migrated
        except OSError as e:                                                    # Incase of other OS error
            print(f"Error: {e}")
            return False                                                        # The data directory was NOT migrated

        # 2. Delete Old Data Path
        if man_dataPath != def_dataPath:                                            # Only delete if it's not the default folder
            try:                                                                    # Try deleting the old data path file tree
                shutil.rmtree(man_dataPath)                                         # Delete file tree at man_dataPath
                print(f"Data Path at '{man_dataPath}' deleted successfully.")
            except FileNotFoundError:                                               # Incase the file tree is missing (somehow?)
                print(f"Error: The directory '{man_dataPath}' does not exist.")
                return False                                                        # The data directory was NOT migrated
            except OSError as e:                                                    # Incase of other OS error
                print(f"Error: {e}. Directory must be empty to use os.rmdir().")
                return False                                                        # The data directory was NOT migrated

        # 3. Ensure a JSON File exists at the Default Data Path
        filename = 'Pointer.json'                                               # Pointer.json is the expected file name
        data = {"man_pointer": os.path.relpath(new_location)}                   # The pointer is stored in the relative data path compared to run directory

        try:                                                                    # Try to open the file in 'w' (write) mode. 
            with open(def_dataPath / filename, 'w') as json_file:               # This will create a new file or overwrite an existing one.
                json.dump(data, json_file, indent=4)                            # Use json.dump() to serialize the Python object and write it to the file.
            print(f"Successfully updated pointer file.")
        except IOError as e:                                                    # Catch I/O errors, such as permission issues or invalid path.
            print(f"Error writing pointer file: {e}")          
            return False                                                        # The data directory was NOT migrated                 
        except Exception as e:                                                  # Catch any other potential exceptions
            print(f"An unexpected error occurred: {e}")
            return False                                                        # The data directory was NOT migrated  

        # 4. Finishing Steps
        man_dataPath = new_location                                             # Set man_DataPath to new_location value
        return True                                                             # The data directory was migrated

# Recover Data Path from Populated Folder
def recover(new_location):
        new_location = new_location = (_scriptDir.parent / pathlib.Path(new_location)).resolve()    # Convert provided file path into Path object
        global man_dataPath                                                                         # Pass man_dataPath by reference into method

        if new_location == def_dataPath:                                                            # If the new location is default file location ("recovering back")
                
                # 1. Delete the JSON File left in the Default Data Path
                try:                                                                    # Try to delete the JSON file
                    man_pointer.unlink()                                                # JSON file unlinked from data tree
                    print(f"JSON file '{man_pointer}' has been deleted successfully.")
                except FileNotFoundError:                                               # If the file is missing (somehow?)
                    print(f"File '{man_pointer}' does not exist.")                   

        else:                                                                           # If the new location is NOT default file location ("recovering out")
        

            # 1. Ensure a JSON File exists at the Default Data Path
            filename = 'Pointer.json'                                               # Pointer.json is the expected file name
            data = {"man_pointer": os.path.relpath(new_location)}                   # The pointer is stored in the relative data path compared to run directory

            try:                                                                    # Try to open the file in 'w' (write) mode. 
                with open(def_dataPath / filename, 'w') as json_file:               # This will create a new file or overwrite an existing one.
                    json.dump(data, json_file, indent=4)                            # Use json.dump() to serialize the Python object and write it to the file.
                print(f"Successfully updated pointer file.")
            except IOError as e:                                                    # Catch I/O errors, such as permission issues or invalid path.
                print(f"Error writing pointer file: {e}")          
                return False                                                        # The data directory was NOT migrated                 
            except Exception as e:                                                  # Catch any other potential exceptions
                print(f"An unexpected error occurred: {e}")
                return False                                                        # The data directory was NOT migrated  
          

        # 2. Finishing Steps - Same for both cases
        man_dataPath = new_location                                             # Reset man_DataPath to new_location value
        return True                                                             # The data directory was migrated

# Get Data Path from outside this script - returns manual data path
def get_data_path():
    return man_dataPath

# This block only runs if the script is executed DIRECTLY
# It is skipped when imported as a module
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="SCADA Data Manager")                              # Description of current parser
    subparsers = parser.add_subparsers(dest="command")                                              # Define a subcommand for each function

    subparsers.add_parser("initDataPath", help="Initialize the data path")                          # initDataPath - no arguments needed

    migrate_parser = subparsers.add_parser("migrate", help="Migrate data to a new location")        # migrate - takes a location argument
    migrate_parser.add_argument("location", type=str, help="Target path to migrate to")

    recover_parser = subparsers.add_parser("recover", help="Recover data from a populated folder")  # recover - takes a location argument
    recover_parser.add_argument("location", type=str, help="Path to recover from")

    # Parse and dispatch
    args = parser.parse_args()

    if args.command == "initDataPath":
        init_data_path()
    elif args.command == "migrate":
        init_data_path()          # Always load state first!
        migrate(args.location)
    elif args.command == "recover":
        init_data_path()          # Always load state first!
        recover(args.location)
    else:
        parser.print_help()