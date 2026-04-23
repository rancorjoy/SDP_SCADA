# ino_utils.py
# This file contains the methods needed to create code for an arduino based on settings and pin modes

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON

from . import print_log

def default_code(board):
    def_code = f"""
            void setup() {{
            // put your setup code here, to run once:
            }}

            void loop() {{
            // put your main code here, to run repeatedly:
            }}
            """
