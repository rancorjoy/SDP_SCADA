import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.reset_input_buffer()
time.sleep(2)

while True:
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').rstrip()
        if line:
            number = int(line)
            print(f"Received: {number}")
            number += 1
            print(f"Sending: {number}")
            ser.write(f"{number}\n".encode('utf-8'))