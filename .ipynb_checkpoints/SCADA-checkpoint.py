# Import Needd Libraries
import pathlib # Object-Oriented File Path Management

# Persistent Data File Location
p = pathlib.Path("/SCADA_Data")

def main():
    print("Test")
    if p.is_dir():
        print(f"The directory exists.")
    else:
        print(f"The directory does not exist or is a file.")