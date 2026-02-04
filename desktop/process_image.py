import cv2
import math
import os
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==============================
# USER INPUT (REAL HEIGHT)
# ==============================
USER_HEIGHT_CM = float(input("Enter your real height (cm): "))

IMAGE_DIR = "data/captured"
MODEL_PATH = "desktop/models/pose_landmarker_lite.task"

# ==============================
# Load image
# ==============================
images = sorted(os.listdir(IMAGE_DIR))
image_path = os.path.join(IMAGE_DIR, images[-1])

image = cv2.imread(image_path)
h, w, _ = image.shape
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# ==============================
# MediaPipe Pose (IMAGE mode)
# ==============================
BaseOptions = python.BaseOptions
PoseLandmarker = vision.PoseLandmarker
PoseLandmarkerOptions = vision.PoseLandmarkerOptions
RunningMode = vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=RunningMode.IMAGE
)

landmarker = PoseLandmarker.create_from_options(options)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
result = landmarker.detect(mp_image)

if not result.pose_landmarks:
    print("❌ No pose detected")
    exit()

lm = result.pose_landmarks[0]

# ==============================
# Helper functions
# ==============================
def px(p1, p2):
    return math.sqrt(
        (p1.x*w - p2.x*w)**2 +
        (p1.y*h - p2.y*h)**2
    )

# ==============================
# LANDMARK INDEXES
# ==============================
NOSE = 0
LS, RS = 11, 12
LE, RE = 13, 14
LW, RW = 15, 16
LH, RH = 23, 24
LA, RA = 27, 28

# ==============================
# HEIGHT (PIXELS → CM SCALE)
# ==============================
pixel_height = px(lm[NOSE], lm[LA])
scale = USER_HEIGHT_CM / pixel_height

# ==============================
# MEASUREMENTS (PIXELS)
# ==============================
measurements_px = {
    "shoulder_width": px(lm[LS], lm[RS]),
    "chest_width": px(lm[LS], lm[RS]) * 0.9,
    "waist_width": px(lm[LH], lm[RH]) * 0.85,
    "hip_width": px(lm[LH], lm[RH]),
    "torso_length": px(lm[LS], lm[LH]),
    "arm_length": px(lm[LS], lm[LW]),
    "leg_length": px(lm[LH], lm[LA])
}

# ==============================
# CONVERT TO CM
# ==============================
measurements_cm = {
    k: round(v * scale, 2)
    for k, v in measurements_px.items()
}

# ==============================
# OUTPUT
# ==============================
print("\n📐 BODY MEASUREMENTS (cm)\n")
for k, v in measurements_cm.items():
    print(f"{k.replace('_',' ').title():<20}: {v} cm")

# ==============================
# VISUAL DEBUG
# ==============================
for p in lm:
    cv2.circle(image, (int(p.x*w), int(p.y*h)), 3, (0,255,0), -1)

cv2.imshow("Pose + Measurements", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
landmarker.close()
