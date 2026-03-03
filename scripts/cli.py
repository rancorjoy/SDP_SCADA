# cli.py
# Manages Input CLI for Flask

                                                # Import Needed Libraries
import requests                                 # For Command Line Interface Window                   

BASE_URL = "http://localhost:5000"              # Flask Server Internal URL

print("SCADA CLI - type 'help' for commands")   # User Help Message

while True:                                     # Continuous Loop...
    user_input = input("> ").strip()            # Get User Input without ">" or spaces
    
    if user_input == "exit":                    # If "exit" (exit command) ->
        break                                   # Close Window
    
    elif user_input == "help":                  # If "help" (help command)
        print("Commands:")                      # Top Row Header:
        print("  help")                         # List All Commands!
        print("  status")
        print("  migrate <path>")
        print("  recover <path>")
        print("  exit")
    
    elif user_input == "status":                    # If "status" (status command)
        r = requests.get(f"{BASE_URL}/status")      # Get Flask Server Status
        print(r.json())                             # Print Flask Server Status
    
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