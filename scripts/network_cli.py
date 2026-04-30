# cli.py
# Manages Input CLI for Flask

                                                # Import Needed Libraries
import shlex                                    # Simple Lexican Analysis for Shell-like Commands
import requests                                 # For Command Line Interface Window     
import json                                     # JSON File Management AND display for CLI    
import time                                     # For event logging       

BASE_URL = "http://192.168.0.50:5000"                  # Flask Server Internal URL

print("SCADA CLI - type 'help' for commands")   # User Help Message

while True:                                     # Loop that runs forever...
    raw = input("> ").strip()                   # Obtain user input without shell command "> "
    if not raw:                                 # If there is no user input...
        continue                                # Continue waiting
    if raw == "exit":                           # If user input == "exit"...
        break                                   #exit the CLI

    try:                                        # Try to render command and arguments
        parts = shlex.split(raw)                # Handles quoted paths with spaces
    except ValueError as e:                     # If there is an exception...
        print(f"Parse error: {e}")              # Print the error and continue running
        continue                                # This way an improper input does not crash the CLI

    cmd, args = parts[0], parts[1:]             # The command is the first part, the rest are arguments

    try:                                                                                        # Try to send the new command to the flask server
        r = requests.post(f"{BASE_URL}/command", json={"cmd": cmd, "args": args}, timeout=10)   # This will timeout after 10 seconds without response
        data = r.json()                                                                         # Obtain the server output json as "r.json"

        if "message" in data:                                                                   # If the json contains a "message" field...
            print(data["message"])                                                              # Print the message only
        elif "result" in data:                                                                  # If the json contains a "result" field...
            print(data["result"])                                                               # Print the result
        elif "dict" in data:                                                                    # If the json only contains a dictionary...
            print(json.dumps(data["dict"], indent=2))                                           # Print it as a json dump (looks nicer to read)
        else:                                                                                   # If the json only contains unlabeled data...
            print(json.dumps(data, indent=2))                                                   # Print it as a json dump (looks nicer to read)

    except requests.exceptions.ConnectionError:                                                 # If the server cannot be reached...
        print("Error: cannot reach SCADA server at", BASE_URL)                                  # Tell the user that the server cannot be reached at the current adress
    except requests.exceptions.Timeout:                                                         # If the server has timed out...
        print("Error: server timed out")                                                        # Tell the user that the server has timed out