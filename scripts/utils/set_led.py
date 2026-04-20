import sys
import os
import time

# Add the Freenove code path to sys.path
sys.path.append('/home/ahmed/Freenove_Computer_Case_Kit_for_Raspberry_Pi/Code')

from expansion import Expansion

def set_color(r, g, b):
    board = Expansion()
    try:
        # Mode 1 is manual RGB control
        board.set_led_mode(1)
        board.set_all_led_color(r, g, b)
        print(f"LEDs set to R:{r} G:{g} B:{b}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        board.end()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        r, g, b = map(int, sys.argv[1:4])
        set_color(r, g, b)
    else:
        print("Usage: python3 set_led.py R G B")
