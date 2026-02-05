import tkinter as tk
from tkinter import filedialog
import shutil
import os
import time

# -----------------------------
# Setup
# -----------------------------
UPLOAD_DIR = "data/uploaded"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Open File Explorer
# -----------------------------
root = tk.Tk()
root.withdraw()  # hide empty tkinter window

print("📂 Select an image from Explorer...")

file_path = filedialog.askopenfilename(
    title="Select your image",
    filetypes=[
        ("Image Files", "*.jpg *.jpeg *.png"),
    ]
)

if not file_path:
    print("❌ No image selected")
    exit()

# -----------------------------
# Save image
# -----------------------------
filename = f"upload_{int(time.time())}.jpg"
dest_path = os.path.join(UPLOAD_DIR, filename)

shutil.copy(file_path, dest_path)

print(f"✅ Image uploaded successfully!")
print(f"📁 Saved at: {dest_path}")
