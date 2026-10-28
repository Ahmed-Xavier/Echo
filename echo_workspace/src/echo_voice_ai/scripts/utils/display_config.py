import sys
import os
import time

freenove_code = os.getenv("FREENOVE_CODE_PATH")
if freenove_code:
    sys.path.append(freenove_code)
from oled import OLED

def display_config():
    oled = OLED()
    try:
        oled.clear()
        oled.draw_text("OpenClaw Config:", position=(0, 0))
        oled.draw_text("Model: Gemini 3 Flash", position=(0, 16))
        oled.draw_text("Fallback: Gemini 2.0", position=(0, 32))
        oled.draw_text("Port: 18789", position=(0, 48))
        oled.show()
        print("Config displayed on OLED.")
        time.sleep(10)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        oled.clear()
        oled.show()

if __name__ == "__main__":
    display_config()
