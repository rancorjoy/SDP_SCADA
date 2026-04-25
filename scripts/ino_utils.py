# ino_utils.py
# This file contains the methods needed to create code for an arduino based on settings and pin modes

# Import Needed Libraries
import os       # Operating System Management
import pathlib  # Object-Oriented File Path Management
import json     # JSON File Management
import shutil   # Shell Utilities (High Level File Operations)
import argparse # Allows Console Use of Functions with Variables
import pickle   # Allows Dictionary to be saved to JSON
import textwrap # Allows Arduino C++ code blocks to be dedented

from . import dcs_dict_utils
from . import print_log

# Get interrupt function for an interrupt (ISR)
# Interrupt Modes: LOW, CHANGE, RISING, FALLING, HIGH (on some boards)
def get_int_func(int_name, cont):
    intr = cont["int_config"][int_name]

    if int_name.startswith("DP"):   # Logic for pin interrupts
        pin_num = int_name[2:]      # Remove DP to get pin number
        code_str = f"attachInterrupt(digitalPinToInterrupt({pin_num}), {intr["ISR_name"]}, {intr["mode"]});\n"
    return code_str

# Get the interrupt definititions for the setup of each interrupt pin (in setup)
def get_int_funcs(cont):
    codestring = f""
    for key in cont["int_config"]:
        if cont["int_config"][key]["enabled"] and key.startswith("DP"):
            codestring += get_int_func(key, cont)
    return codestring

# Get the interrupt ISR for an interrupt
def get_ISR(int_name, cont):

    code_str = f""
    if int_name.startswith("DP"):       # Logic for digital interrupts
        code_str = textwrap.dedent(f"""
        // ISR for {int_name}
        void {cont["int_config"][int_name]["ISR_name"]}(){{

        }}
        """)
    if int_name.startswith("Timer"):    # Logic for timer interrupts
        code_str = textwrap.dedent(f"""
        // ISR for {int_name}
        ISR({cont["int_config"][int_name]["ISR_name"]}){{

        }}
        """)
    return code_str

# Get all interrupt ISRs (before setup)
def get_ISRs(cont):
    codestring = f""
    for key in cont["int_config"]:
        if cont["int_config"][key]["enabled"]:
            codestring += get_ISR(key, cont)
    return codestring

# Get a block of code to define a single software point at the top of the script
def get_var(cont, point_name):
    point = cont["software_points"][point_name]
    code_str = textwrap.dedent(f"Point<{point["type"]}> {point_name} = {{{point["default"]}, {point["hold_val"]}, false}};\n")
    return code_str

# Get a block of Arduino code (at the top) that adds all software points
def get_vars(cont):
    code_str = f""

    point_dict = cont["software_points"]
    pin_dict = cont["pin_config"]
    tim_dict = cont["timers"]

    for key, val in point_dict.items():
        if not val["hardware"]:                     # software point are always active
            code_str += get_var(cont, key)

        elif key in pin_dict:                       # pin hardware point
            if pin_dict[key]["enabled"]:
                code_str += get_var(cont, key)

        else:                                       # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in tim_dict and tim_dict[timer_name]["enabled"]:
                code_str += get_var(cont, key)
    return code_str

# Get a block of Arduino code that sets the pin mode for a single pin
def get_pin_mode(pin_id, cont):
    pin = cont["pin_config"][pin_id]
    
    prefix = ""                 # By default digital pins need no prefix (DP1 -> 1)
    if pin_id.startswith("AP"): # If the pin is an analog pin
        prefix="A"              # The Arduino IDE needs its name to start with "A"
    prefix += pin_id[2:]        # Add the pin number to the prefix string (pin_id after DP or AP)

    code_str = textwrap.dedent(f"pinMode({prefix}, {pin["direction"]});\n")
    return code_str

# Get a block of Arduino code (in setup) that configures all pin modes
def get_pin_modes(cont):
    code_str = textwrap.dedent(f"""
            // Set Pin Modes for all Enabled Pins
            """)

    for key in cont["pin_config"]:
        if cont["pin_config"][key]["enabled"]:
            code_str += get_pin_mode(key, cont)
    
    return code_str

# Get a block of arduino code (in setup) to start one timer
def get_timer_config(timer_name, cont):
    
    timer = cont["timers"][timer_name]
    timer_num = timer_name[5:]  # The string after the first 5 chars "Timer" -> "num" eg 0
    timer_size = timer["size_bits"]
    timer_mode = timer["mode"]

    code_str = f"// Register Settings for Timer {timer_num}\n"

    if timer_size == 8:
        code_str += f"TCCR{timer_num}A = 0; TCCR{timer_num}B = 0; TCNT{timer_num} = 0;\n"
    else:                       # The timer is 16-bit
        code_str += f"TCCR{timer_num}A = 0; TCCR{timer_num}B = 0; TCCR{timer_num}C = 0; TCNT{timer_num} = 0;\n"
    code_str += f"TCNT{timer_num}  = (uint{timer_size}_t)getPoint(Timer{timer_num}_Preload);\n"

    for ch in timer["channels"]:
        code_str += f"OCR{timer_num}{ch}  = (uint{timer_size}_t)getPoint(Timer{timer_num}_CH{ch}_Comp);\n"
    code_str += f"TCCR{timer_num}B |= (uint8_t)getPoint(Timer{timer_num}_Prescaler);\n"

    wgm_map_8bit = {
        "OVF":                f"// Normal/Overflow mode - WGM bits default to 0\n",
        "CTC":                f"TCCR{timer_num}A |= (1 << WGM{timer_num}1);\n",
        "FAST_PWM":           f"TCCR{timer_num}A |= (1 << WGM{timer_num}1) | (1 << WGM{timer_num}0);\n",
        "PHASE_CORRECT_PWM":  f"TCCR{timer_num}A |= (1 << WGM{timer_num}0);\n",
    }

    wgm_map_16bit = {
        "OVF":                f"// Normal/Overflow mode - WGM bits default to 0\n",
        "CTC":                f"TCCR{timer_num}B |= (1 << WGM{timer_num}2);\n",
        "FAST_PWM":           f"TCCR{timer_num}A |= (1 << WGM{timer_num}1) | (1 << WGM{timer_num}0);\n"
                              f"TCCR{timer_num}B |= (1 << WGM{timer_num}2);\n",
        "PHASE_CORRECT_PWM":  f"TCCR{timer_num}A |= (1 << WGM{timer_num}0);\n",
        "INPUT_CAPTURE":      f"TCCR{timer_num}B |= (1 << WGM{timer_num}3) | (1 << WGM{timer_num}2);\n",
    }

    wgm_map = wgm_map_8bit if timer_size == 8 else wgm_map_16bit
    code_str += wgm_map[timer_mode] + f"\n"

    for key, val in cont["int_config"].items():
        if key.startswith(timer_name) and val["enabled"]:
            if key == f"{timer_name}_OVF":
                code_str += f"TIMSK{timer_num} |= (1 << TOIE{timer_num});\n"
            elif key == f"{timer_name}_COMPA":
                code_str += f"TIMSK{timer_num} |= (1 << OCIE{timer_num}A);\n"
            elif key == f"{timer_name}_COMPB":
                code_str += f"TIMSK{timer_num} |= (1 << OCIE{timer_num}B);\n"
            elif key == f"{timer_name}_COMPC":
                code_str += f"TIMSK{timer_num} |= (1 << OCIE{timer_num}C);\n"
            elif key == f"{timer_name}_CAPT":
                code_str += f"TIMSK{timer_num} |= (1 << ICIE{timer_num});\n"

    code_str += f"\n"
    return code_str
    
# Get a block of code (in setup) to start all timers that are enabled
def get_timer_configs(cont_name, cont):
    timers = cont["timers"]

    code_str = f""

    for key in timers:
        if timers[key]["enabled"]:
            code_str += get_timer_config(key, cont)

    return code_str

def get_code(data_path, cont_name):
    cont = dcs_dict_utils.get_dict(data_path, cont_name)

    def_code = textwrap.dedent(f"""\

// Struct Definition for all Points
template <typename T>
struct Point {{
    T val;
    T hold_val;
    bool hold_en;
}};
                               

// Instantiate all Points
{get_vars(cont)}

// ISR methods - do not touch
{get_ISRs(cont)}

// SCADA required methods - do not touch

// Get the current value of a point based on hold_en
template <typename T>
T getPoint(const volatile Point<T>& p) {{
    return p.hold_en ? p.hold_val : p.val;
}}

void setup() {{

{get_pin_modes(cont)}

// Attach enabled interrupts to pins
{get_int_funcs(cont)}

{get_timer_configs(cont_name, cont)}
}}

void loop() {{

}}
""").strip()
    return def_code
