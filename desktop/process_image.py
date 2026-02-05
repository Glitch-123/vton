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
        return None, "Image not found or invalid format", None

    h, w, _ = img.shape
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    BaseOptions = python.BaseOptions
    PoseLandmarker = vision.PoseLandmarker
    PoseLandmarkerOptions = vision.PoseLandmarkerOptions
    
    # Check explicitly before crashing
    if not os.path.exists(MODEL_PATH):
        return None, f"Model not found at {MODEL_PATH}", None

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE
    )

    landmarker = PoseLandmarker.create_from_options(options)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    res = landmarker.detect(mp_image)

    if not res.pose_landmarks:
        return None, "No pose detected", None

    lm = res.pose_landmarks[0]

    # --- DRAWING LANDMARKS ---
    annotated_img = img.copy()
    
    # Draw logic manually or use mp defaults
    # Using mediapipe drawing utils is easier if available for standard Pose, 
    # but the Task API returns landmarks slightly differently than the old Solution API.
    # We'll manually draw for control or use a helper if we import it.
    # Simple manual draw for key points:
    
    # Colors (Myntra-ish: Pink/Orange/White)
    COLOR_POINT = (0, 255, 0) # Green for valid
    COLOR_LINE = (255, 255, 255)
    
    connections = [
        (11, 12), (11, 13), (13, 15), # Arms
        (12, 14), (14, 16),
        (11, 23), (12, 24), # Torso
        (23, 24),
        (23, 25), (25, 27), # Legs
        (24, 26), (26, 28)
    ]
    
    # Draw Lines
    for start, end in connections:
        if start < len(lm) and end < len(lm):
            p1 = lm[start]
            p2 = lm[end]
            if visible(p1) and visible(p2):
                x1, y1 = int(p1.x * w), int(p1.y * h)
                x2, y2 = int(p2.x * w), int(p2.y * h)
                cv2.line(annotated_img, (x1, y1), (x2, y2), COLOR_LINE, 2)
    
    # Draw Points
    for i, p in enumerate(lm):
        if visible(p):
            cx, cy = int(p.x * w), int(p.y * h)
            cv2.circle(annotated_img, (cx, cy), 4, COLOR_POINT, -1)
            # cv2.putText(annotated_img, str(i), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,0,255), 1)

    # Save Annotated Image
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # Simple robust naming: processed_<original_name>
    filename = f"processed_{os.path.basename(image_path)}"
    annotated_path = os.path.join(processed_dir, filename)
    cv2.imwrite(annotated_path, annotated_img)


    if confidence(lm) < 0.6: 
        return None, "Low confidence pose", annotated_path

    # --- ADVANCED MEASUREMENT LOGIC ---
    
    # helper for euclidean distance
    def dist(i1, i2):
        return px_dist(lm[i1], lm[i2], w, h)

    # 1. Pose Validation (Risk Assessment)
    # Check if shoulder width is too narrow compared to torso height (Side View?)
    shoulder_px_width = abs(lm[11].x - lm[12].x) * w
    torso_px_height = abs((lm[11].y+lm[12].y)/2 - (lm[23].y+lm[24].y)/2) * h
    
    orientation_warning = None
    if shoulder_px_width < 0.45 * torso_px_height:
        orientation_warning = "⚠️ Side/Angled view detected. Results may be inaccurate."

    # 2. Scale Calibration (Pixels per CM)
    # Robust height estimation
    ankles_y = (lm[27].y + lm[28].y) / 2 if (visible(lm[27]) and visible(lm[28])) else None
    
    if ankles_y: 
        # Full Body: Nose (0) to Ankle Midpoint
        px_height_segment = abs(lm[0].y - ankles_y) * h
        # Standard Anatomy: Nose-to-Ankle is ~86% of full height
        px_full_height = px_height_segment / 0.86
    else:
        # Upper Body: Mid-Shoulder to Mid-Hip
        mid_s_y = (lm[11].y + lm[12].y) / 2
        mid_h_y = (lm[23].y + lm[24].y) / 2
        px_torso = abs(mid_s_y - mid_h_y) * h
        # Torso is approx 30% of height
        px_full_height = px_torso / 0.30
    
    scale = height_cm / px_full_height # cm per pixel

    # 3. Clothing Metrics Calculation (Circumference Estimation)
    
    # We measure 2D 'width' from camera. Clothing uses 'Girth' (Circumference).
    # Humans are roughly elliptical. 
    # Girth approx = Width * Multiplier
    # Multiplier varies: Neck ~3.0, Waist ~2.7, Chest ~2.6 (arms block view)
    
    def to_girth(width_cm, multiplier=2.8):
        return width_cm * multiplier

    # A. Shoulders (Bi-acromial Width) - LINEAR
    shoulder_px = dist(11, 12)
    shoulder_width = shoulder_px * scale * 1.0 
    
    # B. Chest (Underarm) - CIRCUMFERENCE
    # Visible width is often reduced by arms or posture.
    chest_px = dist(11, 12) * 0.95 
    chest_width_2d = chest_px * scale
    # Chest depth is significant.
    chest_circ = to_girth(chest_width_2d, 2.7)
    
    # C. Waist (Natural Waist) - CIRCUMFERENCE
    hip_width_px = dist(23, 24)
    # Natural waist is narrower than hips
    waist_px = hip_width_px * 0.82 
    waist_width_2d = waist_px * scale
    waist_circ = to_girth(waist_width_2d, 2.85) # Waists are often more circular
    
    # D. Hips (Widest Point) - CIRCUMFERENCE
    # 23/24 are Iliac crests. Trochanter (widest) is wider.
    hip_bone_width = dist(23, 24) * scale
    hip_max_width = hip_bone_width * 1.15
    hip_circ = to_girth(hip_max_width, 2.9) # Hips are wide and deep
    
    # E. Sleeve Length - LINEAR
    arm_px = dist(11, 13) + dist(13, 15)
    sleeve_length = arm_px * scale
    
    # F. Inseam - LINEAR
    leg_ext = (dist(23, 25) + dist(25, 27)) * scale if ankles_y else 0
    inseam = leg_ext * 0.85 if leg_ext > 0 else 0

    # G. Neck - CIRCUMFERENCE
    # Neck width is approx 38% of shoulder width?
    neck_width = shoulder_width * 0.38
    neck_circ = to_girth(neck_width, 3.0)

    m = {
        "Height (Ref)": height_cm,
        "Shoulder Width": shoulder_width,
        "Chest (Girth)": chest_circ,
        "Waist (Girth)": waist_circ,
        "Hips (Girth)": hip_circ,
        "Neck (Girth)": neck_circ,
        "Sleeve Length": sleeve_length,
        "Inseam": inseam
    }

    # --- ANNOTATE MEASUREMENTS ON IMAGE ---
    # Helper to draw dimension line
    def draw_dim(idx1, idx2, text, offset_y=0):
        if visible(lm[idx1]) and visible(lm[idx2]):
            p1 = (int(lm[idx1].x * w), int(lm[idx1].y * h))
            p2 = (int(lm[idx2].x * w), int(lm[idx2].y * h))
            mid = ((p1[0]+p2[0])//2, (p1[1]+p2[1])//2 + offset_y)
            cv2.line(annotated_img, p1, p2, (0, 255, 255), 2) 
            cv2.putText(annotated_img, text, (mid[0]-40, mid[1]-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

    if orientation_warning:
        cv2.putText(annotated_img, "WARNING: Pose Risk", (20, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    draw_dim(11, 12, f"Sh: {shoulder_width:.1f}", -20)
    draw_dim(23, 24, f"HipBone: {hip_bone_width:.1f}", 20)
    
    # Visualizing Natural Waist (Interpolated)
    wx1 = int( (lm[23].x + (lm[11].x - lm[23].x) * 0.15) * w )
    wy1 = int( (lm[23].y + (lm[11].y - lm[23].y) * 0.15) * h )
    wx2 = int( (lm[24].x + (lm[12].x - lm[24].x) * 0.15) * w )
    wy2 = int( (lm[24].y + (lm[12].y - lm[24].y) * 0.15) * h )
    cv2.line(annotated_img, (wx1, wy1), (wx2, wy2), (255, 0, 255), 2)
    # Label with Girth for user clarity? Or Width? Maybe Girth since that's what they care about.
    # But visually it's a line of width. Let's show "Waist" and user checks text for value.
    cv2.putText(annotated_img, f"Waist", (wx1, wy1-10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
    
    # Optional: Draw Chest Line
    draw_dim(11, 12, "Chest", 40)

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
    return m, None, annotated_path
