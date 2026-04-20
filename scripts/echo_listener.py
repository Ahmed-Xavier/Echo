import pvporcupine
from pvrecorder import PvRecorder
import os
import requests
import subprocess
import time

ACCESS_KEY = "JLK7fhHBwG5Hmp8EQ5xSWjvkJ0AdBNxjcHsW5F5Gf124cvnCG3d6Nw=="
KEYWORD_PATH = "/home/ahmed/.openclaw/workspace/echo_wake_word.ppn"
ELEVENLABS_KEY = "sk_084daee8df779c57a2a5ee3ccac55a247413b2f5ff8a7dd9"
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # George

def say(text):
    print(f"Echo says: {text}")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_multilingual_v2"}
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            with open("/tmp/echo_response.mp3", "wb") as f:
                f.write(resp.content)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "/tmp/echo_response.mp3"])
    except Exception as e:
        print(f"Voice error: {e}")

def run_listener():
    try:
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[KEYWORD_PATH])
        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        recorder.start()

        print("Echo is listening for 'Hey Echo'...")
        
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                print("Wake word detected!")
                say("I am here, Ahmed. How can I help you?")
                # Short pause to prevent re-triggering while speaking
                time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping Echo...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if porcupine: porcupine.delete()
        if recorder: recorder.stop()

if __name__ == "__main__":
    run_listener()
