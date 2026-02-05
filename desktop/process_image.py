import cv2, os, csv, shutil
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pose_utils import *

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Path to the model (in desktop/models)
MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "pose_landmarker_lite.task")

def process_image(image_path, height_cm):
    img = cv2.imread(image_path)
    if img is None:
        return None, "Image not found or invalid format"

    h, w, _ = img.shape
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    BaseOptions = python.BaseOptions
    PoseLandmarker = vision.PoseLandmarker
    PoseLandmarkerOptions = vision.PoseLandmarkerOptions
    
    # Check explicitly before crashing
    if not os.path.exists(MODEL_PATH):
        return None, f"Model not found at {MODEL_PATH}"

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE
    )

    landmarker = PoseLandmarker.create_from_options(options)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    res = landmarker.detect(mp_image)

    if not res.pose_landmarks:
        return None, "No pose detected"

    lm = res.pose_landmarks[0]

    if confidence(lm) < 0.6: # Relaxed slightly
        return None, "Low confidence pose"

    # --- IMPROVED MEASUREMENT LOGIC ---
    
    # helper for distance
    def dist(i1, i2):
        return px_dist(lm[i1], lm[i2], w, h)

    # 1. Calculate Pixels per CM (Scale)
    # Use Eye-level to Ankle-level for height if full body
    # Standard head-to-body ratio is approx 1:7.5 or 1:8
    
    # Determine accessible height in pixels
    # If we have feet, use (Nose Y - Ankle Y) and adjust for Head top/Foot bottom
    # MediaPipe: 0=Nose, 27/28=Ankles, 31/32=Feet tips
    
    # Robust height estimation
    ankles_y = (lm[27].y + lm[28].y) / 2 if (visible(lm[27]) and visible(lm[28])) else None
    
    if ankles_y: # Full body visible
        # Nose to Ankle is approx 85-88% of full height usually
        px_height_segment = abs(lm[0].y - ankles_y) * h
        # Estimated full height in pixels (adding head top and feeet offset)
        px_full_height = px_height_segment * 1.15 
    else:
        # Upper body only fallback (approximate from torso)
        # Torso (Shoulder to Hip) is approx 30% of height
        mid_shoulder_y = (lm[11].y + lm[12].y) / 2
        mid_hip_y = (lm[23].y + lm[24].y) / 2
        px_torso = abs(mid_shoulder_y - mid_hip_y) * h
        px_full_height = px_torso * 3.3  # Rough estimation
    
    scale = height_cm / px_full_height # cm per pixel

    # 2. Width & Girth Estimations (with curvature multipliers)
    # Straight line distance through body is < circumferential diameter
    # We apply multipliers to approximate "size" properly.
    
    # Shoulders
    # Bone-to-bone width (acromial). For "Measure" usually we want garment width.
    shoulder_px = dist(11, 12) 
    shoulder_width = shoulder_px * scale * 1.1 # Multiplier for skin/muscle

    # Chest
    # Interpolated point between shoulder and hip? 
    # Or simple Shoulder width adjusted? 
    # Let's approximate Chest width at armpit level roughly equal to shoulder bone width for men, 
    # often wider/different for women. Simplified:
    chest_px = dist(11, 12) * 0.9  # Roughly underarm width
    chest_width = chest_px * scale * 1.15 # Multiplier for depth

    # Waist
    # Hips in MediaPipe are iliac crestish.
    hip_px = dist(23, 24)
    waist_width = hip_px * scale * 1.15

    # Torso Length (Vertical)
    # Shoulder mid to Hip mid
    mid_s = ((lm[11].x+lm[12].x)/2, (lm[11].y+lm[12].y)/2)
    mid_h = ((lm[23].x+lm[24].x)/2, (lm[23].y+lm[24].y)/2)
    # Manual Euclidean dist since they are coords not landmark objects
    torso_px = math.sqrt(((mid_s[0]-mid_h[0])*w)**2 + ((mid_s[1]-mid_h[1])*h)**2) 
    torso_length = torso_px * scale

    # Arm Length 
    # Shoulder to Wrist
    # Sum segments for better accuracy if arm is bent: Shoulder->Elbow + Elbow->Wrist
    arm_px = dist(11, 13) + dist(13, 15) # Left Arm
    arm_length = arm_px * scale

    m = {
        "Height (Ref)": height_cm,
        "Shoulder Width": shoulder_width,
        "Chest Width": chest_width,
        "Waist Width": waist_width,
        "Torso Length": torso_length,
        "Arm Length": arm_length,
    }

    if ankles_y: # Full body extras
        # Leg: Hip to Ankle (Hip->Knee + Knee->Ankle)
        leg_px = dist(23, 25) + dist(25, 27)
        m["Leg Length"] = leg_px * scale

    # Save CSV
    measurements_dir = os.path.join(PROJECT_ROOT, "data", "measurements")
    os.makedirs(measurements_dir, exist_ok=True)
    csv_path = os.path.join(measurements_dir, "measurements.csv")
    write_header = not os.path.exists(csv_path)

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(m.keys())
        writer.writerow([round(v,2) for v in m.values()])

    landmarker.close()
    return m, None
