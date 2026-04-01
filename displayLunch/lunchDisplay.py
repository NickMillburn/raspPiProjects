#!/usr/bin/env python3
import sys, tkinter as tk

msg = "LUNCH" if len(sys.argv) == 1 else " ".join(sys.argv[1:])

root = tk.Tk()
root.title("Sign")
root.configure(bg="black")
root.attributes("-fullscreen", True)

for key in ("<space>", "q", "<Escape>"):
    root.bind(key, lambda e: root.destroy())

w = root.winfo_screenwidth()
font_px = max(40, w // 8)

label = tk.Label(
    root, text=msg, fg="white", bg="black",
    font=("Arial", font_px, "bold"),
    wraplength=int(w * 0.9),
    justify="center"
)
label.pack(expand=True, fill="both")

root.mainloop()
