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
from . import code_block_utils
from . import print_log


# Get all interupt points
# Then also get all block types used
# Then use block types used to get all dependencies

# Get list of all volatile points
def get_vol_list(curr_dict, controller_name):
    block_lists = code_block_utils.find_lists(curr_dict, controller_name)
    vol_list = []
    for list_key in block_lists:
        if list_key != "setup_blocks" and list_key != "loop_blocks":
            for blk in block_lists[list_key]:
                for pt_key in blk["input_points"]:
                    name = code_block_utils.get_point_name(curr_dict, controller_name, blk["input_points"][pt_key])
                    if name != "?" and name not in vol_list:
                        vol_list.append(name)
                for pt_key in blk["output_points"]:
                    name = code_block_utils.get_point_name(curr_dict, controller_name, blk["output_points"][pt_key])
                    if name != "?" and name not in vol_list:
                        vol_list.append(name)
    return vol_list

# Get all dependancies
def get_depend(data_path, cont_name, block_lib):
    used_blocks = code_block_utils.block_types_used(data_path, cont_name)
    dep_list = []

    for block_type in used_blocks:
        for dep in block_lib[block_type]["dep_list"]:
            if dep not in dep_list:
                dep_list.append(dep)

    code_str = f""
    for dep in dep_list:
        code_str += textwrap.dedent(f"#include <{dep}.h>\n")

    return code_str

# Define all code blocks near top of script
def define_code_blocks(data_path, cont_name, block_lib):
    used_blocks = code_block_utils.block_types_used(data_path, cont_name)
    code_str = f""

    for block_type in used_blocks:
        code_str += get_block_code(block_type, block_lib)

    return code_str


# Get code block equivelent (defined before setup for each detected block type)
def get_block_code(block_type, block_lib):

    # Defaults to void return type
    return_type_str = f"void "
    return_str = f""

    code_str = f""

    # If there are outputs, pain
    if len(block_lib[block_type]["output_points"]) != 0:
        code_str += f"template <"

        for key in block_lib[block_type]["output_points"]:
            code_str += f"typename {key}_t, "
        
        code_str = code_str[:-2] # Remove last comma and space
        code_str += f">\n"

        code_str += f"struct {block_type}_s\n"
        code_str += f"{{\n"

        for key in block_lib[block_type]["output_points"]:
            code_str += f"\t{key}_t {key};\n"

        code_str += f"}};\n"

        return_str = f"return {{"
        for key in block_lib[block_type]["output_points"]:
            return_str += f"{key}, "
        return_str = return_str[:-2] # Remove last comma and space
        return_str += f"}};"

        return_type_str = f"{block_type}_s "
        return_type_str += f"<"
        for key in block_lib[block_type]["output_points"]:
            return_type_str += f"{key}_t, "
        return_type_str = return_type_str[:-2] # Remove last comma and space
        return_type_str += f"> "
    
    code_str += f"template <"
    for key in block_lib[block_type]["input_points"]:
        code_str += f"typename {key}_t, "

    for key in block_lib[block_type]["output_points"]:
        code_str += f"typename {key}_t = {block_lib[block_type]["output_type_case"][key]}, "

    code_str = code_str[:-2] # Remove last comma and space
    code_str += f">\n"

    code_str += f"{return_type_str}{block_type}({get_block_generic_inputs(block_type, block_lib)})\n"
    code_str += f"{{\n"
    code_str += textwrap.indent(get_block_sets(block_type, block_lib), "\t")
    code_str += textwrap.indent(get_block_auto(block_type, block_lib), "\t")
    code_str += textwrap.indent(block_lib[block_type]["code_str"], "\t")
    code_str += textwrap.indent(return_str, "\t")
    code_str += f"\n}}\n\n"
    return code_str

# Get list of code-block generic input arguments (for function)
def get_block_generic_inputs(block_type, block_lib):

    code_str = f""
    for key in block_lib[block_type]["input_points"]:
        code_str += f"{key}_t {key}_p, "
    code_str = code_str[:-2]        # Remove last comma and space
    return code_str

# Get list of code-block generic output arguments (for function)
def get_block_generic_outputs(block_type, block_lib):

    code_str = f""
    for key in block_lib[block_type]["output_points"]:
        code_str += f"{key}_p, "
    code_str = code_str[:-2]        # Remove last comma and space
    return code_str

# Get types for tupple string for code block
def get_block_tupple_str(block_type, block_lib):

    code_str = f""
    for key, val in block_lib[block_type]["output_points"].items():
        code_str += f"{val}, "
    code_str = code_str[:-2]        # Remove last comma and space
    return code_str

# Get variable setting for code block function
def get_block_sets(block_type, block_lib):
    code_str = f""
    for key in block_lib[block_type]["input_points"]:
        code_str += f"{key}_t {key} = {key}_p;\n"
    return code_str

# Assign all output blocks auto type and arbitrary const 0 before calculations
def get_block_auto(block_type, block_lib):
    code_str = f""
    for key in block_lib[block_type]["output_points"]:
        code_str += f"auto {key} = 0;\n"
    return code_str

# Get code block instance usage, placed in a list location
def get_block_inst_code(block_inst, block_lib, curr_dict, cont_name, index):

    code_str = f""
    top_str = f""
    bottom_str = f""

    # If the code block is conditional
    if block_inst["condition"] != None:
        top_str = f"if (getPoint({block_inst["condition"]["_name"]}) {{\n)"
        bottom_str = f"}}\n"

    # If the block has outputs
    if len(block_lib[block_inst["block_type"]]["output_points"]) != 0:

        code_str += f"auto result{index} = {block_inst["block_type"]}("
        for key in block_inst["input_points"]:
            point = code_block_utils.get_point_name_by_value(curr_dict, cont_name, block_inst["input_points"][key])
            code_str += f"getPoint({point}), "

        code_str = code_str[:-2] # Remove last comma and space
        code_str += ");\n"

        for key in block_inst["output_points"]:
            point = code_block_utils.get_point_name_by_value(curr_dict, cont_name, block_inst["output_points"][key])
            code_str += f"setPoint({point}, result{index}.{key});\n"

        code_str += "\n"
        return top_str + code_str + bottom_str

    # If the block has no outputs
    else:

        code_str += f"{block_inst["block_type"]}("
        for key in block_inst["input_points"]:
            point = code_block_utils.get_point_name_by_value(curr_dict, cont_name, block_inst["input_points"][key])
            code_str += f"getPoint({point}), "

        code_str = code_str[:-2] # Remove last comma and space
        code_str += ");\n"

        code_str += "\n"
        return code_str
    
# Print a list of blocks
def get_block_list(block_list, block_lib, curr_dict, cont_name):
    code_str = f""
    index = 0

    for block_inst in block_list:
        code_str += get_block_inst_code(block_inst, block_lib, curr_dict, cont_name, index)
        index += 1

    return code_str

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
def get_ISR(int_name, cont, curr_dict, cont_name, block_lib):

    code_str = f""
    if int_name.startswith("DP"):       # Logic for digital interrupts
        code_str = textwrap.dedent(f"""
        // ISR for {int_name}
        void {cont["int_config"][int_name]["ISR_name"]}(){{
            {get_block_list(cont["int_config"][int_name]["blocks"], block_lib, curr_dict, cont_name)}
        }}
        """)
    if int_name.startswith("Timer"):    # Logic for timer interrupts
        code_str = textwrap.dedent(f"""
        // ISR for {int_name}
        ISR({cont["int_config"][int_name]["ISR_name"]}){{
            {get_block_list(cont["int_config"][int_name]["blocks"], block_lib, curr_dict, cont_name)}
        }}
        """)
    return code_str

# Get all interrupt ISRs (before setup)
def get_ISRs(cont, curr_dict, cont_name, block_lib):
    codestring = f""
    for key in cont["int_config"]:
        if cont["int_config"][key]["enabled"]:
            codestring += get_ISR(key, cont, curr_dict, cont_name, block_lib)
    return codestring

# Get a block of code to define a single software point at the top of the script
def get_var(cont, point_name, curr_dict, controller_name):
    point = cont["software_points"][point_name]
    vol = f""
    vol_list = get_vol_list(curr_dict, controller_name)
    if point_name in vol_list:
        vol = f"volatile "

    if point["const"]: vol = f"constexpr "

    if point["type"] == "int" and point["int_type"] != "":
        code_str = textwrap.dedent(f"{vol}Point<{point["int_type"]}> {point_name} = {{{point["default"]}, 0, false, {point["min"]}, {str(point["min_en"]).lower()}, {point["max"]}, {str(point["max_en"]).lower()}}};\n")
        return code_str
    elif point["type"] == "float" and point["float_type"] != "":
        code_str = textwrap.dedent(f"{vol}Point<{point["float_type"]}> {point_name} = {{{point["default"]}, 0, false, {point["min"]}, {str(point["min_en"]).lower()}, {point["max"]}, {str(point["max_en"]).lower()}}};\n")
        return code_str
    else:
        code_str = textwrap.dedent(f"{vol}Point<{point["type"]}> {point_name} = {{{point["default"]}, 0, false, {point["min"]}, {str(point["min_en"]).lower()}, {point["max"]}, {str(point["max_en"]).lower()}}};\n")
        return code_str

# Get a block of Arduino code (at the top) that adds all software points
def get_vars(cont, curr_dict, controller_name):
    code_str = f""

    point_dict = cont["software_points"]
    pin_dict = cont["pin_config"]
    tim_dict = cont["timers"]

    for key, val in point_dict.items():
        if not val["hardware"]:                     # software point are always active
            code_str += get_var(cont, key, curr_dict, controller_name)

        elif key in pin_dict:                       # pin hardware point
            if pin_dict[key]["enabled"]:
                code_str += get_var(cont, key, curr_dict, controller_name)

        else:                                       # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in tim_dict and tim_dict[timer_name]["enabled"]:
                code_str += get_var(cont, key, curr_dict, controller_name)
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

# Get a code block for a pin being read (start of loop)
def get_pin_read(pin_id, cont):

    code_str = f""
    pin_num = pin_id[2:]

    if cont["pin_config"][pin_id]["direction"] != "OUTPUT" and cont["pin_config"][pin_id]["enabled"]:
        if cont["pin_config"][pin_id]["analog_set"]:
            code_str = f"{pin_id}.val = analogRead({pin_num});\n"
        else:
            code_str = f"{pin_id}.val = digitalRead({pin_num});\n"

    return code_str

# Get a code block for all pin reads (start of loop)
def get_pin_reads(cont):

    code_str = f"// Read all input pins\n"
    for key in cont["pin_config"]:
        code_str += get_pin_read(key, cont)
    
    return code_str

# Get a code block for a pin being written (end of loop)
def get_pin_write(pin_id, cont):

    code_str = f""
    pin_num = pin_id[2:]

    if cont["pin_config"][pin_id]["direction"] == "OUTPUT" and cont["pin_config"][pin_id]["enabled"]:
        if pin_id.startswith("DP"):
            if cont["pin_config"][pin_id]["pwm_set"] == True:
                code_str = f"analogWrite({pin_num}, getPoint({pin_id}));\n"
            else:
                code_str = f"digitalWrite({pin_num}, getPoint({pin_id}));\n"
        elif cont["pin_config"][pin_id]["analog_set"] == False:
            code_str = f"digitalWrite({pin_num}, getPoint({pin_id}));\n"

    return code_str

# Get a code block for all pin writes (end of loop)
def get_pin_writes(cont):

    code_str = f"// Write all output pins\n"
    for key in cont["pin_config"]:
        code_str += get_pin_write(key, cont)

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

# Get block of code for one array instance
def get_array(cont, array_name):
    this_array = cont["arrays"][array_name]
    code_str = f"{this_array["type"]} {this_array["_name"]}[{this_array["size_point"]["_name"]}.val];\n"
    return code_str

# Get block of code for all defined arrays
def get_arrays(cont):
    code_str = f""
    for key in cont["arrays"]:
        code_str += get_array(cont, key)
    return code_str

# Get block of code to check hold_val for one point
def get_hold_point(cont, point_name):
    point = cont["software_points"][point_name]
    g_type = point["type"]

    if g_type == "bool":
        return textwrap.indent(f"if (name == \"{point_name}\") {point_name}.hold_val = (bool)(val == \"true\");\n", "\t\t")
    
    elif g_type == "int":
        s_type = point["int_type"]
        if s_type == "" or s_type == None:
            s_type = "int"
        return textwrap.indent(f"if (name == \"{point_name}\") {point_name}.hold_val = ({s_type})val.toInt();\n", "\t\t")
    
    elif g_type == "float":
        s_type = point["float_type"]
        if s_type == "" or s_type == None:
            s_type = "float"
        return textwrap.indent(f"if (name == \"{point_name}\") {point_name}.hold_val = ({s_type})val.toFloat();\n", "\t\t")

# Get block of code to check all hold_vals vs points
def get_hold_points(cont):
    code_str = f""

    for key, val in cont["software_points"].items():
        if not val["hardware"]:                             # software point are always active
            code_str += get_hold_point(cont, key)

        elif key in cont["pin_config"]:                     # pin hardware point
            if cont["pin_config"][key]["enabled"]:
                code_str += get_hold_point(cont, key)

        else:                                       # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in cont["timers"] and cont["timers"][timer_name]["enabled"]:
                code_str += get_hold_point(cont, key)

    return code_str

# Get block of code to check all hold_ens vs points
def get_hold_en_points(cont):
    code_str = f""
    
    for key, val in cont["software_points"].items():
        if not val["hardware"]:                             # software point are always active
            code_str += textwrap.indent(f"if (name == \"{key}\") {key}.hold_en = val;\n","\t\t")

        elif key in cont["pin_config"]:                     # pin hardware point
            if cont["pin_config"][key]["enabled"]:
                code_str += textwrap.indent(f"if (name == \"{key}\") {key}.hold_en = val;\n","\t\t")

        else:                                               # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in cont["timers"] and cont["timers"][timer_name]["enabled"]:
                code_str += textwrap.indent(f"if (name == \"{key}\") {key}.hold_en = val;\n","\t\t")

    return code_str

# Get block of code to transmit data out to SCADA
def get_write_block(cont):
    code_str = f""
    
    for key, val in cont["software_points"].items():
        if not val["hardware"]:                             # software point are always active
            code_str += textwrap.indent(f"Serial.print(\"{key} \");\nSerial.println(getPoint({key}));\n", "\t\t")

        elif key in cont["pin_config"]:                     # pin hardware point
            if cont["pin_config"][key]["enabled"]:
                code_str += textwrap.indent(f"Serial.print(\"{key} \");\nSerial.println(getPoint({key}));\n", "\t\t")

        else:                                               # timer hardware point
            timer_name = key.split('_')[0]
            if timer_name in cont["timers"] and cont["timers"][timer_name]["enabled"]:
                code_str += textwrap.indent(f"Serial.print(\"{key} \");\nSerial.println(getPoint({key}));\n", "\t\t")

    return code_str

# Function that assembles generated code for Aduino
def get_code(data_path, cont_name, block_lib, curr_dict):
    cont = dcs_dict_utils.get_dict(data_path, cont_name)

    def_code = textwrap.dedent(f"""\
// Include Libraries if any needed
{get_depend(data_path, cont_name, block_lib)}

// Struct Definition for all Points
template <typename T>
struct Point {{
    T val;
    T hold_val;
    bool hold_en;
    T min;
    bool min_en;
    T max;
    bool max_en;
}};
                               

// Instantiate all Points
{get_vars(cont, curr_dict, cont_name)}

// SCADA required methods - do not touch

// Get the current value of a point based on hold_en
template <typename T>
T getPoint(const volatile Point<T>& p) {{
    T val = p.hold_en ? p.hold_val : p.val;
    if (p.min_en && val < p.min) {{
        val = p.min;
    }}

    if (p.max_en && val > p.max) {{
        val = p.max;
    }}

    return val;
}}
// Set the current value of a point with min/max checking
template <typename T>
void setPoint(volatile Point<T>& p, T new_val) {{
    T constrained = new_val;

    if (p.min_en && constrained < p.min) {{
        constrained = p.min;
    }}

    if (p.max_en && constrained > p.max) {{
        constrained = p.max;
    }}

    p.val = constrained;
}}

// Instantiate all arrays
{get_arrays(curr_dict[cont_name])}

// Code block functions
{define_code_blocks(data_path, cont_name, block_lib)}

// ISR methods - do not touch
{get_ISRs(cont, curr_dict, cont_name, block_lib)}

void setup() {{
Serial.begin(9600); // Initialize serial communication
cli(); // Disable interrupts

{get_pin_modes(cont)}

// Attach enabled interrupts to pins
{get_int_funcs(cont)}

{get_timer_configs(cont_name, cont)}
sei(); // Re-enable interrupts

{get_block_list(curr_dict[cont_name]["setup_blocks"], block_lib, curr_dict, cont_name)}

}}

unsigned long lastSend_var = 0;

void loop() {{
{get_pin_reads(cont)}

// Set Holds
if (Serial.available()) {{
    String cmd = Serial.readStringUntil('\\n');
    cmd.trim();

    // Hold Enable Command Received
    if (cmd.startsWith("hold_en ")) {{
        String args = cmd.substring(8);
        int sp = args.indexOf(' ');
        String name = args.substring(0, sp);
        bool val = args.substring(sp + 1) == "true";

{get_hold_en_points(cont)}
    }}
      
        // Hold Value Command Received
        else if (cmd.startsWith("hold ")) {{
        String args = cmd.substring(5);
        int sp = args.indexOf(' ');
        String name = args.substring(0, sp);
        String val = args.substring(sp + 1);

{get_hold_points(cont)}
    }}
  }}

// Run all instances of code blocks and store results
{get_block_list(curr_dict[cont_name]["loop_blocks"], block_lib, curr_dict, cont_name)}

// Write all output pin values
{get_pin_writes(cont)}


    if (millis() - lastSend_var >= 100) {{
        // Transmit all values to SCADA over serial connection
{get_write_block(cont)}
        lastSend_var = millis();
    }}

}}
""").strip()
    return def_code
