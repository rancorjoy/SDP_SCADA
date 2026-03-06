# cli.py
# Manages Input CLI for Flask

                                                # Import Needed Libraries
import requests                                 # For Command Line Interface Window     
import json                                     # JSON File Management AND display for CLI           

BASE_URL = "http://localhost:5000"              # Flask Server Internal URL

print("SCADA CLI - type 'help' for commands")   # User Help Message

while True:                                     # Continuous Loop...
    user_input = input("> ").strip()            # Get User Input without ">" or spaces
    
    if user_input == "exit":                    # If "exit" (exit command) ->
        break                                   # Close Window
    
    elif user_input == "help":                  # If "help" (help command) - List All Commands!
        print("General Commands:")                      
        print("  help :             \t Displays a list of all valid commands") 
        print("  exit :              \t Exit CLI and disable SCADA server")    
        print("  status :           \t Displays the network status of the SCADA server\n")

        print("Data Path Commands:")
        print("  init :             \t Initializes the persistent data path")
        print("  migrate <path> :   \t Migrates the persistent data path to specified location <path>")
        print("  recover <path> :   \t Recovers the persistent data path at specified location <path>\n")

        print("Serial Commands:")
        print("  list_serial_ports : \t Lists all detected serial connections to the SCADA server")
        print("\n")
    
    elif user_input == "status":                    # If "status" (status command)
        r = requests.get(f"{BASE_URL}/status")      # Get Flask Server Status
        print(r.json())                             # Print Flask Server Status
    
    elif user_input.startswith("init"):                                 # If "init" (initialize command)
        r = requests.post(f"{BASE_URL}/initialize")                     # Pass Command Data to SCADA.py Server
        print(r.json())                                                 # Print the Sent Command

    elif user_input.startswith("list_serial_ports"):                    # If "list_serial_ports" (list all connected devices)
        r = requests.post(f"{BASE_URL}/listSerialPorts")                # Pass Command Data to SCADA.py Server
        print(json.dumps(r.json(), indent=4))                           # Print the Sent Command

    elif user_input.startswith("migrate "):                             # If "migrate ..." (migrate command)
        path = user_input.split(" ", 1)[1]                              # Recover path using break character (space)
        r = requests.post(f"{BASE_URL}/migrate", json={"path": path})   # Pass Command Data to SCADA.py Server
        print(r.json())                                                 # Print the Sent Command
    
    elif user_input.startswith("recover "):                             # If "recover ..." (recover command)
        path = user_input.split(" ", 1)[1]                              # Recover path using break character (space)
        r = requests.post(f"{BASE_URL}/recover", json={"path": path})   # Pass Command Data to SCADA.py Server
        print(r.json())                                                 # Print the Sent Command
    
    else:                                                                       # If another input is entered
        print(f"Unknown command: '{user_input}'. Type 'help' for commands.")    # Tell user command is unkown