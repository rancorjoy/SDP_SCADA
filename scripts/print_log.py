# print_log.py

# Import Needed Libraries
import time                 # Gets date and time from system
import shutil               # Shell Utilities

def pL(event_cat, event_type, event, user, admin, details):                                    
    time_str = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}]"
    left = f"{time_str} {event_cat} {event_type}: {event}"
    if admin:
        right = f"[{user}]"
    else:
        right = f"<{user}>"

    term_width = shutil.get_terminal_size().columns
    offset = 4;
    print(f"{left.ljust(term_width - len(right) - offset)}{right}")

    if details is not None:
        print(f"Details: {details}\n")