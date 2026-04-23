#!/usr/bin/env python3
import pvporcupine
from pvrecorder import PvRecorder
import subprocess
import os
import time
import wave
import struct
import requests
import speech_recognition as sr

# --- CONFIG ---
PICOVOICE_KEY = "JLK7fhHBwG5Hmp8EQ5xSWjvkJ0AdBNxjcHsW5F5Gf124cvnCG3d6Nw=="
KEYWORD_PATH = "/home/ahmed/.openclaw/workspace/echo_wake_word.ppn"
ELEVENLABS_KEY = "sk_084daee8df779c57a2a5ee3ccac55a247413b2f5ff8a7dd9"
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb" # George
TELEGRAM_ID = "1139225059"

def say(text):
    print(f"Echo: {text}")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_multilingual_v2"}
    try:
        resp = requests.post(url, json=data, headers=headers)
        if resp.status_code == 200:
            with open("/tmp/echo_reply.mp3", "wb") as f:
                f.write(resp.content)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "/tmp/echo_reply.mp3"], stderr=subprocess.DEVNULL)
        else:
            print(f"ElevenLabs Error: {resp.status_code}")
    except Exception as e:
        print(f"Vocal Error: {e}")

def record_fixed_duration(recorder, seconds=5):
    print(f"Recording for {seconds}s...")
    frames = []
    # Play a quick acknowledge tone
    subprocess.run(["ffplay", "-nodisp", "-autoexit", "/usr/share/sounds/alsa/Front_Center.wav"], stderr=subprocess.DEVNULL)
    
    start_time = time.time()
    while time.time() - start_time < seconds:
        frame = recorder.read()
        frames.append(frame)
            
    path = "/tmp/query.wav"
    with wave.open(path, 'wb') as wf:
        wf.setparams((1, 2, 16000, 0, "NONE", "NONE"))
        # Flatten frames and pack as 16-bit integers
        all_samples = [s for f in frames for s in f]
        wf.writeframes(struct.pack("h" * len(all_samples), *all_samples))
    return path

def main():
    porcupine = pvporcupine.create(access_key=PICOVOICE_KEY, keyword_paths=[KEYWORD_PATH])
    recorder = PvRecorder(frame_length=porcupine.frame_length)
    recognizer = sr.Recognizer()

    print("Echo V4.1 Active (Fixed Duration - No VAD)...")

    try:
        while True:
            recorder.start()
            print("Listening...")
            while True:
                pcm = recorder.read()
                if porcupine.process(pcm) >= 0:
                    print("Wake word detected!")
                    recorder.stop()
                    audio_path = record_fixed_duration(recorder, seconds=5)
                    
                    # STT
                    try:
                        with sr.AudioFile(audio_path) as source:
                            audio_data = recognizer.record(source)
                            query = recognizer.recognize_google(audio_data)
                            print(f"User: {query}")
                            
                            # Log to Telegram
                            subprocess.run(["openclaw", "message", "send", "--target", f"telegram:{TELEGRAM_ID}", "--message", f"🗣️ Heard: \"{query}\""])
                            
                            # Agent processing
                            subprocess.run([
                                "openclaw", "agent", "--agent", "main", "--message", query, "--thinking", "low"
                            ])
                            
                    except sr.UnknownValueError:
                        print("Google Speech Recognition could not understand audio")
                        say("I'm sorry, I couldn't quite hear that.")
                    except sr.RequestError as e:
                        print(f"Could not request results from Google Speech Recognition service; {e}")
                        say("I'm having trouble connecting to my translation service.")
                    except Exception as e:
                        print(f"STT Error: {e}")
                        say("Internal logic error during transcription.")
                    
                    break
    except Exception as e:
        print(f"Main Loop Error: {e}")
    finally:
        recorder.stop()
        porcupine.delete()

if __name__ == "__main__":
    main()
