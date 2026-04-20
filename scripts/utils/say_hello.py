import requests
import subprocess
import os

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
            with open("/tmp/echo_hello.mp3", "wb") as f:
                f.write(resp.content)
            # Use ffplay to play the audio on the Pi's speakers
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "/tmp/echo_hello.mp3"])
        else:
            print(f"Error from ElevenLabs: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Voice error: {e}")

if __name__ == "__main__":
    say("Hello Ahmed. I am here. Don't worry about the ESP32 for now, I'm still listening.")
