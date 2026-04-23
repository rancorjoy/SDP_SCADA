#current_state.py is a simple data structure to pass data between the main thread and FLASK

import threading
from dataclasses import dataclass

@dataclass
class CurrentState:
    current_dcs  : dict
    current_dict : dict
    current_dict_lock : threading.Lock