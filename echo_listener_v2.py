import pvporcupine
from pvrecorder import PvRecorder
import os
import requests
import subprocess
import time
import wave
import struct

# --- CONFIG ---
ACCESS_KEY = "JLK7fhHBwG5Hmp8EQ5xSWjvkJ0AdBNxjcHsW5F5Gf124cvnCG3d6Nw=="
KEYWORD_PATH = "/home/ahmed/.openclaw/workspace/echo_wake_word.ppn"
ELEVENLABS_KEY = "sk_084daee8df779c57a2a5ee3ccac55a247413b2f5ff8a7dd9"
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # George
TELEGRAM_CHAT_ID = "1139225059"
# --- --- --- ---

def say(text):
    print(f"Echo: {text}")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_multilingual_v2"}
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            with open("/tmp/echo_voice.mp3", "wb") as f:
                f.write(resp.content)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "/tmp/echo_voice.mp3"])
    except Exception as e:
        print(f"Speak error: {e}")

def record_command(recorder, seconds=5):
    print(f"Recording for {seconds}s...")
    path = "/tmp/command.wav"
    with wave.open(path, 'wb') as wf:
        wf.setparams((1, 2, 16000, 512, "NONE", "NONE"))
        start = time.time()
        while time.time() - start < seconds:
            wf.writeframes(struct.pack("h" * len(recorder.read()), *recorder.read()))
    return path

def process_with_openclaw(audio_path):
    # For now, we notify Telegram that we heard a voice command
    # Full STT + LLM pipeline being installed (Whisper)
    cmd = f"openclaw message send --target telegram:{TELEGRAM_CHAT_ID} --message '🎙️ Voice command received. Processing...' --media {audio_path}"
    subprocess.run(cmd, shell=True)
    return "I am processing your voice command through my Telegram bridge now."

def run_loop():
    porcupine = None
    recorder = None
    try:
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[KEYWORD_PATH])
        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        
        print("Echo Loop Active...")
        
        while True:
            recorder.start()
            while True:
                pcm = recorder.read()
                if porcupine.process(pcm) >= 0:
                    print("Wake Word!")
                    recorder.stop()
                    # Acknowledge
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", "/usr/share/sounds/alsa/Front_Center.wav"], stderr=subprocess.DEVNULL)
                    
                    audio_file = record_command(recorder)
                    response_text = process_with_openclaw(audio_file)
                    say(response_text)
                    break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if porcupine: porcupine.delete()
        if recorder: recorder.stop()

if __name__ == "__main__":
    run_loop()
