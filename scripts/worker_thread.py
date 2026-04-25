# worker_thread
# This software thread asynchronously manages serial communication and SQL logging for one Arduino

# Import Needed Libraries
import serial
import struct
import queue
import threading
import time
from . import cobs_utils

