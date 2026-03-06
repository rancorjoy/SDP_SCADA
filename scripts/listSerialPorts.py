# listSerialPorts.py

# Import Needed Libraries
import serial                                               # Serial Communications over USB<->USB
import serial.tools.list_ports                              # Serial communication tools for port detection

def list_serial_ports():                                    # Function that list all serial connections to SCADA server
    ports = serial.tools.list_ports.comports()              # Collect all ports in serial.tools.list_ports.comports()
    result = []                           
    for port in ports:
        result.append({
            "port": port.device,
            "description": port.description,
            "hwid": port.hwid,
            "manufacturer": port.manufacturer,
            "serial_number": port.serial_number,
            "vid": port.vid,
            "pid": port.pid
        })
    return result                                           # Return the list

if __name__ == "__main__":                                  # Main function call
    ports = list_serial_ports()
    for port in ports:
        print(port)