import tkinter as tk
from tkinter import filedialog, messagebox
import os, shutil, sys
import subprocess
from process_image import process_image

# --- CONFIGURATION ---
# Get absolute path to the project root (one level up from this script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Define data directories using absolute paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CAPTURED_DIR = os.path.join(DATA_DIR, "captured")
UPLOADED_DIR = os.path.join(DATA_DIR, "uploaded")

# Ensure directories exist
os.makedirs(CAPTURED_DIR, exist_ok=True)
os.makedirs(UPLOADED_DIR, exist_ok=True)

IMAGE_PATH = None

def open_camera():
    global IMAGE_PATH
    # Run capture_image.py from the project root so paths align
    # capture_image.py is expected to be in 'desktop/capture_image.py' relative to root
    capture_script = os.path.join(SCRIPT_DIR, "capture_image.py")
    
    # We run with cwd=PROJECT_ROOT to maintain consistency
    subprocess.run([sys.executable, capture_script], cwd=PROJECT_ROOT)
    
    # Check for captured images
    if os.path.exists(CAPTURED_DIR):
        imgs = sorted(os.listdir(CAPTURED_DIR))
        if imgs:
            IMAGE_PATH = os.path.join(CAPTURED_DIR, imgs[-1])
            status.set(f"Camera image captured: {imgs[-1]}")
        else:
            status.set("No image captured")
    else:
        status.set("Error: Capture directory missing")

def upload_image():
    global IMAGE_PATH
    path = filedialog.askopenfilename(
        filetypes=[("Images", "*.jpg *.png *.jpeg")]
    )
    if not path:
        return

    # Copy to uploaded directory
    filename = os.path.basename(path)
    dest_path = os.path.join(UPLOADED_DIR, filename) # Keep original name or use fixed?
    # Original code used fixed "upload.jpg", keeping that for simplicity if desired, 
    # but unique names are better. Let's stick to simple "upload.jpg" to match previous logic logic?
    # The previous logic was: IMAGE_PATH = "data/uploaded/upload.jpg"
    dest_path = os.path.join(UPLOADED_DIR, "upload.jpg")
    
    shutil.copy(path, dest_path)
    IMAGE_PATH = dest_path
    status.set("Image uploaded")

def process():
    if not IMAGE_PATH:
        messagebox.showerror("Error", "No image selected")
        return

    try:
        height = float(height_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Enter valid height (cm)")
        return

    # process_image expects a path. It also loads a model. 
    # We'll need to make sure process_image can find its model.
    # See next step for fixing process_image.py
    result, error = process_image(IMAGE_PATH, height)
    
    output.delete("1.0", tk.END)

    if error:
        output.insert(tk.END, f"❌ {error}")
    else:
        output.insert(tk.END, "📐 BODY MEASUREMENTS (cm)\n\n")
        for k,v in result.items():
            output.insert(tk.END, f"{k:20}: {v:.2f}\n")

# ---------- UI ----------
root = tk.Tk()
root.title("Virtual Try-On – Measurement System")
root.geometry("450x550")

tk.Label(root, text="VIRTUAL TRY-ON", font=("Arial", 18, "bold")).pack(pady=10)

tk.Button(root, text="📸 Use Camera", width=30, command=open_camera).pack(pady=5)
tk.Button(root, text="🖼 Upload Image", width=30, command=upload_image).pack(pady=5)

tk.Label(root, text="Enter Height (cm):").pack(pady=5)
height_entry = tk.Entry(root)
height_entry.pack()

tk.Button(root, text="📐 Calculate Measurements", width=30, command=process).pack(pady=10)

output = tk.Text(root, height=15, width=50)
output.pack(pady=10)

status = tk.StringVar()
status.set("Ready")
tk.Label(root, textvariable=status, fg="green").pack()

root.mainloop()
