import cv2, os, sys, csv, shutil, tkinter as tk
from tkinter import filedialog
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pose_utils import *

MODE = sys.argv[1]  # captured / uploaded
MODEL_PATH = "desktop/models/pose_landmarker_lite.task"

# ---------- IMAGE SELECTION ----------
if MODE == "captured":
    imgs = sorted(os.listdir("data/captured"))
    if not imgs:
        print("❌ No captured image"); exit()
    image_path = os.path.join("data/captured", imgs[-1])

elif MODE == "uploaded":
    os.makedirs("data/uploaded", exist_ok=True)
    root = tk.Tk(); root.withdraw()
    src = filedialog.askopenfilename(filetypes=[("Images","*.jpg *.png")])
    if not src:
        exit()
    image_path = "data/uploaded/upload.jpg"
    shutil.copy(src, image_path)

else:
    exit()

# ---------- LOAD IMAGE ----------
img = cv2.imread(image_path)
h, w, _ = img.shape
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# ---------- MEDIAPIPE ----------
BaseOptions = python.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.IMAGE
)

landmarker = PoseLandmarker.create_from_options(options)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
res = landmarker.detect(mp_image)

if not res.pose_landmarks:
    print("❌ No pose detected"); exit()

lm = res.pose_landmarks[0]

# ---------- VALIDATION ----------
if confidence(lm) < 0.7:
    print("❌ Low confidence pose"); exit()

bt = body_type(lm)
if bt == "reject":
    print("❌ Bad framing"); exit()

height_cm = float(input("Enter your height (cm): "))

# ---------- SCALE ----------
if bt == "full":
    px_height = px_dist(lm[HEAD], lm[LA], w, h)
else:
    px_height = px_dist(lm[LS], lm[LH], w, h) * 2.3

scale = height_cm / px_height

# ---------- MEASUREMENTS ----------
m = {}

m["shoulder_width"] = px_dist(lm[LS], lm[RS], w, h) * scale
m["chest_width"] = px_dist(lm[LE], lm[RE], w, h) * scale
m["waist_width"] = px_dist(lm[LH], lm[RH], w, h) * scale
m["torso_length"] = px_dist(lm[LS], lm[LH], w, h) * scale
m["arm_length"] = px_dist(lm[LS], lm[LW], w, h) * scale

if bt == "full":
    m["hip_width"] = px_dist(lm[LH], lm[RH], w, h) * scale
    m["leg_length"] = px_dist(lm[LH], lm[LA], w, h) * scale

# ---------- SAVE ----------
os.makedirs("data/measurements", exist_ok=True)
csv_path = "data/measurements/measurements.csv"

write_header = not os.path.exists(csv_path)

with open(csv_path, "a", newline="") as f:
    writer = csv.writer(f)
    if write_header:
        writer.writerow(m.keys())
    writer.writerow([round(v,2) for v in m.values()])

# ---------- DISPLAY ----------
print("\n📐 BODY MEASUREMENTS (cm)\n")
for k,v in m.items():
    print(f"{k.replace('_',' ').title():20}: {v:.2f}")

landmarker.close()
