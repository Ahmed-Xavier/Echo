#!/usr/bin/env python3
from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk

STATE_FILE = Path("/tmp/echo_face_state")
FACE_ROOT = Path("/home/ahmed/echo_runtime/bmo_face_source/faces")

WIDTH = 800
HEIGHT = 480
FPS = 8
BG = "black"

STATE_MAP = {
    "idle": "idle",
    "listening": "listening",
    "capturing": "capturing",
    "thinking": "thinking",
    "speaking": "speaking",
    "error": "error",
    "warmup": "warmup",
}


class EchoFace:
    def __init__(self, root):
        self.root = root
        self.root.title("Echo Face")
        self.root.configure(bg=BG)

        # Managed window: fullscreen on start, but NOT override-redirect.
        # This keeps the window manager in control, so minimizing/switching can work.
        self.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")
        self.root.resizable(True, True)
        self.root.attributes("-fullscreen", True)

        # Controls:
        # Escape leaves fullscreen and returns to a normal window.
        # Double-click toggles fullscreen.
        # Ctrl+Q closes if needed.
        self.root.bind("<Escape>", self.leave_fullscreen)
        self.root.bind("<Double-Button-1>", self.toggle_fullscreen)
        self.root.bind("<Control-q>", lambda e: self.root.destroy())
        self.root.bind("<Control-Q>", lambda e: self.root.destroy())

        self.label = tk.Label(
            root,
            bg=BG,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
        )
        self.label.pack(fill="both", expand=True)

        self.frames = {}
        self.state = "idle"
        self.last_state = None
        self.index = 0

        self.load_frames()
        STATE_FILE.write_text("idle")
        self.tick()

    def leave_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)
        self.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")

    def toggle_fullscreen(self, event=None):
        current = bool(self.root.attributes("-fullscreen"))
        self.root.attributes("-fullscreen", not current)
        if current:
            self.root.geometry(f"{WIDTH}x{HEIGHT}+0+0")

    def load_frames(self):
        for state, folder_name in STATE_MAP.items():
            folder = FACE_ROOT / folder_name
            files = sorted(folder.glob("*.png"))
            loaded = []

            for file in files:
                img = Image.open(file).convert("RGBA")
                img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
                loaded.append(ImageTk.PhotoImage(img))

            self.frames[state] = loaded
            print(f"[face] {state}: {len(loaded)} frame(s)", flush=True)

        if not self.frames.get("idle"):
            raise RuntimeError(f"No idle frames found in {FACE_ROOT / 'idle'}")

    def read_state(self):
        try:
            state = STATE_FILE.read_text().strip().lower()
        except Exception:
            state = "idle"

        if state not in self.frames or not self.frames[state]:
            state = "idle"

        return state

    def tick(self):
        state = self.read_state()

        if state != self.last_state:
            self.index = 0
            self.last_state = state
            print(f"[face] state -> {state}", flush=True)

        frames = self.frames.get(state) or self.frames["idle"]
        frame = frames[self.index % len(frames)]

        self.label.configure(image=frame)
        self.label.image = frame

        self.index += 1
        self.root.after(int(1000 / FPS), self.tick)


def main():
    root = tk.Tk()
    EchoFace(root)
    root.mainloop()


if __name__ == "__main__":
    main()
