import tkinter as tk
import json
import os

def show_config():
    root = tk.Tk()
    root.title("Echo Configuration")
    
    # Force full screen for the touchscreen
    root.attributes('-fullscreen', True)
    root.configure(bg='black')

    try:
        with open('/home/ahmed/.openclaw/openclaw.json', 'r') as f:
            config = json.load(f)
            
        primary = config.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "N/A")
        fallback = config.get("agents", {}).get("defaults", {}).get("model", {}).get("fallbacks", ["N/A"])[0]
        port = config.get("gateway", {}).get("port", "18789")
        
        display_text = (
            f"SYSTEM CONFIGURATION\n"
            f"--------------------\n"
            f"Primary: {primary}\n"
            f"Fallback: {fallback}\n"
            f"Gateway Port: {port}\n"
            f"Workspace: {config.get('agents', {}).get('defaults', {}).get('workspace', 'N/A')}\n\n"
            f"Status: ONLINE"
        )
    except Exception as e:
        display_text = f"Error reading config: {e}"

    label = tk.Label(
        root, 
        text=display_text, 
        fg='cyan', 
        bg='black', 
        font=('Courier', 18), 
        justify=tk.LEFT,
        padx=20,
        pady=20
    )
    label.pack(expand=True)

    # Quit on tap
    root.bind("<Button-1>", lambda e: root.destroy())
    
    # Auto-close after 30 seconds
    root.after(30000, root.destroy)
    
    root.mainloop()

if __name__ == "__main__":
    show_config()
