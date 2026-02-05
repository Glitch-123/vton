import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os, shutil, sys
import subprocess
from process_image import process_image

# Attempt to import customtkinter for modern look
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    BaseClass = ctk.CTk
    ButtonClass = ctk.CTkButton
    LabelClass = ctk.CTkLabel
    EntryClass = ctk.CTkEntry
    FrameClass = ctk.CTkScrollableFrame
except ImportError:
    # Fallback to standard tkinter
    BaseClass = tk.Tk
    ButtonClass = tk.Button
    LabelClass = tk.Label
    EntryClass = tk.Entry
    FrameClass = tk.Frame

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CAPTURED_DIR = os.path.join(DATA_DIR, "captured")
UPLOADED_DIR = os.path.join(DATA_DIR, "uploaded")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

for d in [CAPTURED_DIR, UPLOADED_DIR, PROCESSED_DIR]:
    os.makedirs(d, exist_ok=True)

class TryOnApp(BaseClass):
    def __init__(self):
        super().__init__()
        self.title("Virtual Try-On System | Myntra Style")
        self.geometry("1100x700")
        
        # Variables
        self.image_path = None
        self.display_image = None
        
        # Layout: Split 60% Image (Left), 40% Panel (Right)
        if "customtkinter" in sys.modules:
            self.grid_columnconfigure(0, weight=3) # Left
            self.grid_columnconfigure(1, weight=2) # Right
            self.grid_rowconfigure(0, weight=1)
        
        # --- LEFT PANEL (IMAGE) ---
        self.left_frame = tk.Frame(self, bg="#1a1a1a") if "customtkinter" not in sys.modules else ctk.CTkFrame(self, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        self.img_label = tk.Label(self.left_frame, bg="#1a1a1a", text="No Image Selected", fg="white")
        self.img_label.pack(expand=True, fill="both", padx=20, pady=20)

        # --- RIGHT PANEL (CONTROLS) ---
        self.right_frame = tk.Frame(self, bg="#2b2b2b") if "customtkinter" not in sys.modules else ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Header
        header = LabelClass(self.right_frame, text="VIRTUAL TRY-ON", font=("Roboto Medium", 24))
        header.pack(pady=(40, 20), padx=20, anchor="w")
        
        # Action Buttons
        self.btn_camera = ButtonClass(self.right_frame, text="📸 Take Photo", command=self.open_camera)
        if "customtkinter" in sys.modules:
             self.btn_camera.configure(width=200, height=40)
        else:
             self.btn_camera.configure(width=20)

        self.btn_camera.pack(pady=10, padx=20)
        
        self.btn_upload = ButtonClass(self.right_frame, text="📤 Upload Image", command=self.upload_image)
        if "customtkinter" in sys.modules:
             self.btn_upload.configure(width=200, height=40)
        else:
             self.btn_upload.configure(width=20)

        self.btn_upload.pack(pady=10, padx=20)
        
        # Height Input
        LabelClass(self.right_frame, text="Height (cm):").pack(pady=(20, 5), padx=20, anchor="w")
        self.height_entry = EntryClass(self.right_frame)
        self.height_entry.pack(pady=5, padx=20, fill="x")
        # Default removed as per request
        # self.height_entry.insert(0, "170")
        
        # ---------------------------------------------
        # Action Buttons Area
        # ---------------------------------------------
        
        # 1. GENERATE FIT (Placeholder for future)
        self.btn_generate = ButtonClass(self.right_frame, text="👕 Generate Fit (Coming Soon)", command=self.generate_fit_placeholder)
        if "customtkinter" in sys.modules:
            self.btn_generate.configure(fg_color="#555", text_color="#aaa", width=200, height=50, state="disabled")
        else:
            self.btn_generate.configure(bg="gray", fg="white", width=20, state="disabled")
        self.btn_generate.pack(pady=(30, 10), padx=20)

        # 2. SEE MEASUREMENTS (Active)
        self.btn_measure = ButtonClass(self.right_frame, text="📏 See Measurements", command=self.process_measurements)
        if "customtkinter" in sys.modules:
            self.btn_measure.configure(fg_color="#ff3f6c", text_color="white", width=200, height=50) # Myntra Pink
        else:
            self.btn_measure.configure(bg="pink", fg="black", width=20)
        self.btn_measure.pack(pady=10, padx=20)
        
        # Results Area
        if "customtkinter" in sys.modules:
            self.results_text = ctk.CTkTextbox(self.right_frame, height=350, fg_color="#333", text_color="white", font=("Consolas", 14), wrap="word")
        else:
            self.results_text = tk.Text(self.right_frame, height=20, bg="#333", fg="white", bd=0, font=("Consolas", 12), wrap="word")
            
        self.results_text.pack(pady=20, padx=20, fill="both", expand=True)

    def load_image(self, path, update_text=True):
        self.image_path = path
        # Resize for display
        img = Image.open(path)
        
        # Calculate aspect ratio to fit in Left Frame (approx 600x600 visible)
        display_w, display_h = 600, 650
        ratio = min(display_w/img.width, display_h/img.height)
        new_size = (int(img.width*ratio), int(img.height*ratio))
        
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img_resized)
        
        self.img_label.configure(image=self.tk_image, text="")
        
        # Clear text only if requested (new upload), otherwise keep measurements
        if update_text:
             self.results_text.delete("1.0", tk.END)
             self.results_text.insert(tk.END, "Image loaded.\n\nClick 'See Measurements' to analyze body metrics.\n")

    def open_camera(self):
        capture_script = os.path.join(SCRIPT_DIR, "capture_image.py")
        subprocess.run([sys.executable, capture_script], cwd=PROJECT_ROOT)
        
        if os.path.exists(CAPTURED_DIR):
            imgs = sorted(os.listdir(CAPTURED_DIR))
            if imgs:
                latest = os.path.join(CAPTURED_DIR, imgs[-1])
                self.load_image(latest)

    def upload_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            dest = os.path.join(UPLOADED_DIR, "upload.jpg")
            shutil.copy(path, dest)
            self.load_image(dest)
            
    def generate_fit_placeholder(self):
        messagebox.showinfo("Coming Soon", "Virtual Garment Try-On feature is under development.")

    def process_measurements(self):
        if not self.image_path:
            messagebox.showerror("Error", "Please select an image first.")
            return
            
        try:
            h = float(self.height_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid Height")
            return
            
        # Call processing
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Analyzing Body Structure...\n")
        self.update_idletasks()
        
        measurements, error, processed_img_path = process_image(self.image_path, h)
        
        if error and not measurements: # Fatal Error
            self.results_text.insert(tk.END, f"\n❌ ERROR: {error}\n")
            if processed_img_path:
                 self.load_image(processed_img_path, update_text=False)
            return
        
        # Soft Warning (e.g. Risk Case: Side View)
        warning_msg = ""
        if error: 
            warning_msg = f"\n⚠️ NOTE: {error}\n"
        
        # --- SIZE RECOMMENDATION LOGIC ---
        # Data is in CM. Convert to Inches for lookup.
        chest_cm = measurements.get("Chest (Girth)", 0)
        waist_cm = measurements.get("Waist (Girth)", 0)
        
        chest_in = chest_cm / 2.54
        
        # User defined Standard:
        # XS: 32-34
        # S: 34-36
        # M: 38-40
        # L: 40-42
        # XL: 42-44
        # XXL: 44-46
        
        size = "Unknown"
        if chest_in < 34: size = "XS"
        elif 34 <= chest_in < 36: size = "S"
        elif 36 <= chest_in < 38: size = "S/M" # Gap handling
        elif 38 <= chest_in < 40: size = "M"
        elif 40 <= chest_in < 42: size = "L"
        elif 42 <= chest_in < 44: size = "XL"
        elif 44 <= chest_in < 46: size = "XXL"
        else: size = "3XL+"
            
        # Show Results
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, f"👕 RECOMMENDED SIZE: {size}\n")
        self.results_text.insert(tk.END, f"(Based on Chest: {chest_in:.1f}\")\n")
        
        if warning_msg:
             self.results_text.insert(tk.END, warning_msg)
             
        self.results_text.insert(tk.END, "="*30 + "\n\n")
        self.results_text.insert(tk.END, "📏 DETAILED METRICS\n" + "-"*30 + "\n")
        
        # Order of display (New Keys)
        order = [
            "Shoulder Width", 
            "Chest (Girth)", 
            "Waist (Girth)", 
            "Hips (Girth)", 
            "Neck (Girth)",
            "Sleeve Length", 
            "Inseam"
        ]
        
        for k in order:
            if k in measurements:
                val = measurements[k]
                val_in = val / 2.54
                # Show both CM and INCH
                self.results_text.insert(tk.END, f"{k:15}: {val:.1f} cm ({val_in:.1f}\")\n")
        
        # Add others if any
        for k, v in measurements.items():
            if k not in order and k != "Height (Ref)":
                self.results_text.insert(tk.END, f"{k:15}: {v:.1f} cm\n")
            
        # Show Annotated Image
        if processed_img_path and os.path.exists(processed_img_path):
            self.load_image(processed_img_path, update_text=False)

if __name__ == "__main__":
    app = TryOnApp()
    app.mainloop()
