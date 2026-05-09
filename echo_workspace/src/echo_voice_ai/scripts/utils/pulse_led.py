import sys
import os
import time

sys.path.append('/home/ahmed/Freenove_Computer_Case_Kit_for_Raspberry_Pi/Code')
from expansion import Expansion

def pulse_blue():
    board = Expansion()
    try:
        board.set_led_mode(1)
        # Pulse blue like a heartbeat
        for i in range(3):
            for b in range(0, 255, 10):
                board.set_all_led_color(0, 0, b)
                time.sleep(0.02)
            for b in range(255, -1, -10):
                board.set_all_led_color(0, 0, b)
                time.sleep(0.02)
        print("Pulse complete.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        board.end()

if __name__ == "__main__":
    pulse_blue()
