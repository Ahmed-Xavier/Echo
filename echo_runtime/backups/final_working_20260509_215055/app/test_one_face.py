#!/usr/bin/env python3
import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path

img_path = Path("/home/ahmed/echo_runtime/bmo_face_source/faces/idle/idle 01.png")

root = tk.Tk()
root.geometry("800x480+0+0")
root.configure(bg="black")

img = Image.open(img_path).convert("RGBA")
img = img.resize((800, 480))

photo = ImageTk.PhotoImage(img)
label = tk.Label(root, image=photo, bg="black")
label.image = photo
label.pack(fill="both", expand=True)

root.mainloop()
