This is the codebase for the SDP SCADA/SDP Project for Cal Poly Pomona Fall 2025 and Spring 2026. This project is under the supervision of Professor Olsen and the ECE department.

Code Files:
The file SCADA.py is the entry point program that should be run on the Raspberry Pi to initiate the SCADA server/DCS node behavior. The scripts folder contains python scripts that are accessed by the entry point but can be run seperately for debugging or SCADA server back-end needs, this folder contains the following scripts:

- unoFlash takes a text argument and concatinates a program <unoHead, arg, unoTail> and then programs an arduino uno at the selected port with this code. The text file unoHead contains...
